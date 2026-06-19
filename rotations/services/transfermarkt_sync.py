"""Sync latest injuries from Transfermarkt."""
from __future__ import annotations

import logging
import re
import time
import unicodedata
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from rotations.models import DataSyncLog, InjuryAssessment, InjuryRecord, Player

logger = logging.getLogger(__name__)

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
TM_SOURCE = "Transfermarkt"

CLUB_TRANSFERMARKT_IDS = {
    "ARS": 11,
    "AVL": 405,
    "BOU": 989,
    "BRE": 1148,
    "BHA": 1237,
    "BUR": 1132,
    "CHE": 631,
    "CRY": 873,
    "EVE": 29,
    "FUL": 931,
    "IPS": 677,
    "LEI": 1003,
    "LIV": 31,
    "MCI": 281,
    "MUN": 985,
    "NEW": 762,
    "NFO": 703,
    "SOU": 180,
    "SUN": 289,
    "TOT": 148,
    "WHU": 379,
    "WOL": 543,
}

BODY_PART_KEYWORDS = {
    "knee": InjuryRecord.BodyPart.KNEE,
    "knie": InjuryRecord.BodyPart.KNEE,
    "hamstring": InjuryRecord.BodyPart.HAMSTRING,
    "muskelverletzung": InjuryRecord.BodyPart.HAMSTRING,
    "thigh": InjuryRecord.BodyPart.HAMSTRING,
    "ankle": InjuryRecord.BodyPart.ANKLE,
    "sprunggelenk": InjuryRecord.BodyPart.ANKLE,
    "achilles": InjuryRecord.BodyPart.ANKLE,
    "groin": InjuryRecord.BodyPart.GROIN,
    "calf": InjuryRecord.BodyPart.CALF,
    "wade": InjuryRecord.BodyPart.CALF,
    "shoulder": InjuryRecord.BodyPart.SHOULDER,
    "back": InjuryRecord.BodyPart.BACK,
    "head": InjuryRecord.BodyPart.HEAD,
    "concussion": InjuryRecord.BodyPart.HEAD,
    "hip": InjuryRecord.BodyPart.GROIN,
}


def _request_delay() -> None:
    time.sleep(getattr(settings, "TRANSFERMARKT_REQUEST_DELAY", 0.35))


def fetch_url(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    timeout = getattr(settings, "TRANSFERMARKT_TIMEOUT", 30)
    retries = getattr(settings, "TRANSFERMARKT_RETRIES", 3)
    last_error: urllib.error.URLError | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return response.read().decode("utf-8", "replace")
        except urllib.error.URLError as exc:
            last_error = exc
            if attempt < retries - 1:
                time.sleep(1.5 * (attempt + 1))
    if last_error:
        raise last_error
    raise urllib.error.URLError("unknown transfermarkt error")


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = re.sub(r"[^a-zA-Z\s]", " ", value).lower()
    return " ".join(value.split())


def parse_tm_date(value: str) -> date | None:
    value = value.strip()
    for fmt in ("%d/%m/%Y", "%d.%m.%Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def parse_days_out(value: str) -> int:
    match = re.search(r"(\d+)", value or "")
    return int(match.group(1)) if match else 0


def infer_body_part(injury_type: str) -> str:
    lowered = injury_type.lower()
    for keyword, body_part in BODY_PART_KEYWORDS.items():
        if keyword in lowered:
            return body_part
    return InjuryRecord.BodyPart.OTHER


def infer_severity(days_out: int) -> str:
    if days_out <= 7:
        return InjuryRecord.Severity.MINOR
    if days_out <= 21:
        return InjuryRecord.Severity.MODERATE
    return InjuryRecord.Severity.SEVERE


def strip_html(value: str) -> str:
    return " ".join(re.sub(r"<[^>]+>", " ", value).split())


def parse_injury_rows(html: str) -> list[dict]:
    rows = re.findall(r'<tr[^>]*class="[^"]*(?:odd|even)[^"]*"[^>]*>(.*?)</tr>', html, re.S)
    injuries = []
    for row in rows:
        cells = [strip_html(cell) for cell in re.findall(r"<td[^>]*>(.*?)</td>", row, re.S)]
        cells = [cell for cell in cells if cell]
        if len(cells) < 5:
            continue
        if cells[0].lower() in {"season", "saison"}:
            continue
        injury_date = parse_tm_date(cells[2])
        if not injury_date:
            continue
        days_out = parse_days_out(cells[4])
        injuries.append(
            {
                "season": cells[0],
                "injury_type": cells[1],
                "injury_date": injury_date,
                "recovery_date": parse_tm_date(cells[3]),
                "days_out": days_out or max(1, parse_days_out(cells[4])),
                "matches_missed": int(re.search(r"(\d+)", cells[5]).group(1))
                if len(cells) > 5 and re.search(r"(\d+)", cells[5])
                else max(1, days_out // 7 if days_out else 1),
            }
        )
    return injuries


def fetch_player_injuries(tm_id: int) -> list[dict]:
    url = f"https://www.transfermarkt.com/player/verletzungen/spieler/{tm_id}"
    _request_delay()
    html = fetch_url(url)
    return parse_injury_rows(html)


def fetch_club_squad(tm_club_id: int) -> dict[str, int]:
    season_id = getattr(settings, "TRANSFERMARKT_SEASON_ID", 2024)
    url = (
        "https://www.transfermarkt.com/club/kader/verein/"
        f"{tm_club_id}/saison_id/{season_id}"
    )
    _request_delay()
    html = fetch_url(url)
    squad: dict[str, int] = {}
    for tm_id, name in re.findall(r'/profil/spieler/(\d+)[^>]*>([^<]+)<', html):
        squad[normalize_name(name)] = int(tm_id)
    return squad


def search_transfermarkt_id(full_name: str) -> int | None:
    query = urllib.parse.quote(full_name)
    url = f"https://www.transfermarkt.com/schnellsuche/ergebnis/schnellsuche?query={query}"
    _request_delay()
    try:
        html = fetch_url(url)
    except urllib.error.URLError:
        return None
    matches = re.findall(r'/profil/spieler/(\d+)[^>]*title="([^"]+)"', html)
    target = normalize_name(full_name)
    for tm_id, name in matches:
        if normalize_name(name) == target:
            return int(tm_id)
    if matches:
        return int(matches[0][0])
    return None


def resolve_transfermarkt_id(player: Player, squad_map: dict[str, int]) -> int | None:
    if player.transfermarkt_id:
        return player.transfermarkt_id

    normalized = normalize_name(player.full_name)
    if normalized in squad_map:
        return squad_map[normalized]

    parts = normalized.split()
    if len(parts) >= 2:
        short = f"{parts[0]} {parts[-1]}"
        if short in squad_map:
            return squad_map[short]
        last_name = parts[-1]
        candidates = [
            tm_id
            for name, tm_id in squad_map.items()
            if name.split() and name.split()[-1] == last_name
        ]
        if len(candidates) == 1:
            return candidates[0]
        first_name = parts[0]
        candidates = [
            tm_id
            for name, tm_id in squad_map.items()
            if len(name.split()) >= 2
            and name.split()[0] == first_name
            and name.split()[-1] == last_name
        ]
        if len(candidates) == 1:
            return candidates[0]

    return search_transfermarkt_id(player.full_name)


def apply_no_injury_record(player: Player, tm_id: int) -> InjuryRecord:
    today = timezone.localdate()
    season_start = date(today.year if today.month >= 7 else today.year - 1, 8, 1)

    player.injury_records.filter(description__startswith=f"{TM_SOURCE}:").delete()
    record = InjuryRecord.objects.create(
        player=player,
        injury_date=season_start,
        body_part=InjuryRecord.BodyPart.OTHER,
        injury_type="Нет зарегистрированных травм",
        severity=InjuryRecord.Severity.MINOR,
        days_out=0,
        matches_missed=0,
        recovery_date=season_start,
        treatment="",
        description=f"{TM_SOURCE}: история травм отсутствует",
    )
    player.transfermarkt_id = tm_id
    player.last_injury_date = None
    player.season_injuries = 0
    player.career_injuries = 0
    player.previous_injuries = 0
    player.injury_history_score = 0
    player.is_available = True
    player.save(
        update_fields=[
            "transfermarkt_id",
            "last_injury_date",
            "season_injuries",
            "career_injuries",
            "previous_injuries",
            "injury_history_score",
            "is_available",
        ]
    )
    return record


def current_season_label() -> str:
    today = timezone.localdate()
    if today.month >= 7:
        return f"{today.year % 100:02d}/{(today.year + 1) % 100:02d}"
    return f"{(today.year - 1) % 100:02d}/{today.year % 100:02d}"


def apply_injury_to_player(player: Player, injuries: list[dict], tm_id: int) -> InjuryRecord:
    latest = injuries[0]
    season_label = current_season_label()
    season_injuries = sum(1 for item in injuries if item["season"] == season_label)
    career_injuries = len(injuries)

    body_part = infer_body_part(latest["injury_type"])
    days_out = latest["days_out"] or 1
    severity = infer_severity(days_out)
    recovery_date = latest["recovery_date"] or latest["injury_date"] + timedelta(days=days_out)
    today = timezone.localdate()

    player.injury_records.filter(description__startswith=f"{TM_SOURCE}:").delete()
    record = InjuryRecord.objects.create(
        player=player,
        injury_date=latest["injury_date"],
        body_part=body_part,
        injury_type=latest["injury_type"][:80],
        severity=severity,
        days_out=days_out,
        matches_missed=latest["matches_missed"],
        recovery_date=recovery_date,
        treatment="",
        description=f"{TM_SOURCE}: {latest['injury_type']}",
    )

    player.transfermarkt_id = tm_id
    player.last_injury_date = latest["injury_date"]
    player.season_injuries = season_injuries
    player.career_injuries = max(career_injuries, season_injuries)
    player.previous_injuries = player.career_injuries
    player.injury_history_score = min(100, player.career_injuries * 8)
    player.is_available = recovery_date <= today
    player.save(
        update_fields=[
            "transfermarkt_id",
            "last_injury_date",
            "season_injuries",
            "career_injuries",
            "previous_injuries",
            "injury_history_score",
            "is_available",
        ]
    )
    return record


def sync_player_injury(player: Player, squad_map: dict[str, int] | None = None) -> bool:
    squad_map = squad_map or {}
    tm_id = resolve_transfermarkt_id(player, squad_map)
    if not tm_id:
        return False

    injuries = fetch_player_injuries(tm_id)
    if injuries:
        apply_injury_to_player(player, injuries, tm_id)
    else:
        apply_no_injury_record(player, tm_id)
    return True


def sync_transfermarkt_injuries(
    *,
    force: bool = False,
    batch_size: int | None = None,
    club_short_name: str | None = None,
) -> DataSyncLog:
    lock_key = "apl_transfermarkt_sync_lock"
    if cache.get(lock_key) and not force:
        return DataSyncLog.objects.filter(source="transfermarkt").first()

    cache.set(lock_key, True, timeout=getattr(settings, "TRANSFERMARKT_SYNC_LOCK_SECONDS", 3600))
    batch_size = batch_size or getattr(settings, "TRANSFERMARKT_SYNC_BATCH_SIZE", 9999)

    try:
        queryset = Player.objects.filter(data_source=Player.DataSource.FPL).select_related("club")
        if club_short_name:
            queryset = queryset.filter(club__short_name=club_short_name)
        elif not force:
            queryset = queryset.annotate(injury_count=Count("injury_records")).filter(injury_count=0)

        players = list(queryset[:batch_size])
        synced = 0
        failed = 0
        squad_cache: dict[str, dict[str, int]] = {}

        for player in players:
            club_id = CLUB_TRANSFERMARKT_IDS.get(player.club.short_name)
            squad_map: dict[str, int] = {}
            if club_id:
                if player.club.short_name not in squad_cache:
                    try:
                        squad_cache[player.club.short_name] = fetch_club_squad(club_id)
                    except urllib.error.URLError as exc:
                        logger.warning("Transfermarkt squad fetch failed for %s: %s", player.club.short_name, exc)
                        squad_cache[player.club.short_name] = {}
                squad_map = squad_cache[player.club.short_name]

            try:
                if sync_player_injury(player, squad_map):
                    synced += 1
                else:
                    failed += 1
            except urllib.error.URLError as exc:
                logger.warning("Transfermarkt sync failed for %s: %s", player.full_name, exc)
                failed += 1

        status = DataSyncLog.Status.SUCCESS if synced else DataSyncLog.Status.FAILED
        message = f"Transfermarkt: обновлено {synced} игроков, не найдено {failed}."
        return DataSyncLog.objects.create(
            source="transfermarkt",
            status=status,
            players_synced=synced,
            clubs_synced=len(squad_cache),
            message=message,
        )
    finally:
        cache.delete(lock_key)


def ensure_transfermarkt_injuries(force: bool = False) -> DataSyncLog | None:
    batch_size = getattr(settings, "TRANSFERMARKT_AUTO_BATCH_SIZE", 0)
    if batch_size <= 0 and not force:
        return DataSyncLog.objects.filter(source="transfermarkt").first()

    missing = (
        Player.objects.filter(data_source=Player.DataSource.FPL)
        .annotate(injury_count=Count("injury_records"))
        .filter(injury_count=0)
        .count()
    )
    if missing == 0 and not force:
        return DataSyncLog.objects.filter(source="transfermarkt", status=DataSyncLog.Status.SUCCESS).first()

    batch_size = batch_size or getattr(settings, "TRANSFERMARKT_SYNC_BATCH_SIZE", 9999)
    return sync_transfermarkt_injuries(force=force, batch_size=batch_size)
