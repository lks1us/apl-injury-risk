"""Sync Premier League squads from the public Fantasy Premier League API."""
from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone

from rotations.models import Club, DataSyncLog, InjuryAssessment, InjuryRecord, Player

logger = logging.getLogger(__name__)

FPL_BOOTSTRAP_URL = "https://fantasy.premierleague.com/api/bootstrap-static/"
POSITION_MAP = {
    1: Player.Position.GOALKEEPER,
    2: Player.Position.DEFENDER,
    3: Player.Position.MIDFIELDER,
    4: Player.Position.FORWARD,
}
CLUB_META = {
    "ARS": ("London", "Emirates Stadium", Decimal("28.50")),
    "AVL": ("Birmingham", "Villa Park", Decimal("22.60")),
    "BOU": ("Bournemouth", "Vitality Stadium", Decimal("16.40")),
    "BRE": ("London", "Gtech Community Stadium", Decimal("17.80")),
    "BHA": ("Brighton", "Amex Stadium", Decimal("18.90")),
    "BUR": ("Burnley", "Turf Moor", Decimal("14.20")),
    "CHE": ("London", "Stamford Bridge", Decimal("32.40")),
    "CRY": ("London", "Selhurst Park", Decimal("19.50")),
    "EVE": ("Liverpool", "Goodison Park", Decimal("21.30")),
    "FUL": ("London", "Craven Cottage", Decimal("17.10")),
    "IPS": ("Ipswich", "Portman Road", Decimal("13.80")),
    "LEI": ("Leicester", "King Power Stadium", Decimal("18.70")),
    "LIV": ("Liverpool", "Anfield", Decimal("30.75")),
    "MCI": ("Manchester", "Etihad Stadium", Decimal("35.00")),
    "MUN": ("Manchester", "Old Trafford", Decimal("31.20")),
    "NEW": ("Newcastle upon Tyne", "St James' Park", Decimal("24.80")),
    "NFO": ("Nottingham", "City Ground", Decimal("18.40")),
    "SOU": ("Southampton", "St Mary's Stadium", Decimal("16.90")),
    "TOT": ("London", "Tottenham Hotspur Stadium", Decimal("27.20")),
    "WHU": ("London", "London Stadium", Decimal("20.60")),
    "WOL": ("Wolverhampton", "Molineux Stadium", Decimal("17.50")),
}
BODY_PART_KEYWORDS = {
    "knee": InjuryRecord.BodyPart.KNEE,
    "hamstring": InjuryRecord.BodyPart.HAMSTRING,
    "ankle": InjuryRecord.BodyPart.ANKLE,
    "groin": InjuryRecord.BodyPart.GROIN,
    "calf": InjuryRecord.BodyPart.CALF,
    "shoulder": InjuryRecord.BodyPart.SHOULDER,
    "back": InjuryRecord.BodyPart.BACK,
    "head": InjuryRecord.BodyPart.HEAD,
    "concussion": InjuryRecord.BodyPart.HEAD,
    "achilles": InjuryRecord.BodyPart.ANKLE,
    "thigh": InjuryRecord.BodyPart.HAMSTRING,
}


def fetch_fpl_payload() -> dict:
    request = urllib.request.Request(
        getattr(settings, "FPL_API_URL", FPL_BOOTSTRAP_URL),
        headers={"User-Agent": "APL-Injury-Risk/1.0"},
    )
    timeout = getattr(settings, "FPL_API_TIMEOUT", 30)
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _stable_int(seed: str, minimum: int, maximum: int) -> int:
    span = maximum - minimum + 1
    return minimum + (hash(seed) % span)


def _parse_birth_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def _calc_age(birth_date: date | None) -> int:
    if not birth_date:
        return 24
    today = timezone.localdate()
    age = today.year - birth_date.year
    if (today.month, today.day) < (birth_date.month, birth_date.day):
        age -= 1
    return max(16, min(45, age))


def _parse_news_date(value: str | None) -> date | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).date()
    except ValueError:
        return None


def _infer_body_part(news: str) -> str:
    lowered = news.lower()
    for keyword, body_part in BODY_PART_KEYWORDS.items():
        if keyword in lowered:
            return body_part
    return InjuryRecord.BodyPart.OTHER


def _infer_severity(status: str, chance: int | None) -> str:
    if status == "i":
        if chance is not None and chance <= 25:
            return InjuryRecord.Severity.SEVERE
        return InjuryRecord.Severity.MODERATE
    if status == "d":
        return InjuryRecord.Severity.MINOR
    return InjuryRecord.Severity.MINOR


def _derive_injury_stats(fpl_player: dict) -> tuple[int, int, date | None, bool]:
    status = fpl_player.get("status") or "a"
    player_id = fpl_player["id"]
    news = (fpl_player.get("news") or "").strip()
    news_date = _parse_news_date(fpl_player.get("news_added"))
    chance = fpl_player.get("chance_of_playing_this_round")

    career_injuries = _stable_int(f"fpl-career-{player_id}", 1, 14)
    season_injuries = 0
    last_injury_date = None
    is_available = status == "a" and (chance is None or chance >= 75)

    if status in {"i", "d"} or "injury" in news.lower():
        season_injuries = max(1, _stable_int(f"fpl-season-{player_id}", 1, 4))
        last_injury_date = news_date or (timezone.localdate() - timedelta(days=_stable_int(f"fpl-days-{player_id}", 7, 120)))
        is_available = False
    elif status in {"u", "s"}:
        is_available = False

    return season_injuries, career_injuries, last_injury_date, is_available


def _player_full_name(fpl_player: dict) -> str:
    known = (fpl_player.get("known_name") or "").strip()
    if known:
        return known
    first = (fpl_player.get("first_name") or "").strip()
    second = (fpl_player.get("second_name") or "").strip()
    full_name = f"{first} {second}".strip()
    return full_name or fpl_player.get("web_name") or f"Player {fpl_player['id']}"


def _upsert_clubs(teams: list[dict]) -> dict[int, Club]:
    clubs_by_fpl_id: dict[int, Club] = {}
    for team in teams:
        short_name = team["short_name"]
        city, stadium, budget = CLUB_META.get(
            short_name,
            ("England", f"{team['name']} Stadium", Decimal("18.00")),
        )
        defaults = {
            "name": team["name"],
            "short_name": short_name,
            "city": city,
            "stadium": stadium,
            "medical_budget": budget,
            "external_id": team["id"],
        }
        club = Club.objects.filter(external_id=team["id"]).first()
        if not club:
            club = Club.objects.filter(short_name=short_name).first()
        if club:
            for field, value in defaults.items():
                setattr(club, field, value)
            club.save()
        else:
            club = Club.objects.create(**defaults)
        clubs_by_fpl_id[team["id"]] = club
    return clubs_by_fpl_id


def _assessment_metrics(player: Player) -> dict[str, int]:
    fatigue = min(100, 35 + player.season_minutes // 45 + player.season_injuries * 8)
    stability = max(15, 100 - player.career_injuries * 4)
    previous = min(100, player.career_injuries * 7 + player.season_injuries * 5)
    recovery = max(10, 100 - player.season_injuries * 12 - (0 if player.is_available else 25))
    return {
        "muscle_fatigue": fatigue,
        "joint_stability": stability,
        "previous_injury_factor": previous,
        "recovery_score": recovery,
    }


def _ensure_assessment(player: Player, previous_minutes: int, previous_injuries: int) -> None:
    today = timezone.localdate()
    latest = player.latest_assessment
    if latest and latest.date == today:
        return
    if latest and abs(player.season_minutes - previous_minutes) < 45 and player.season_injuries == previous_injuries:
        return

    metrics = _assessment_metrics(player)
    InjuryAssessment.objects.create(
        player=player,
        date=today,
        notes="Автооценка после синхронизации с FPL.",
        **metrics,
    )


def _ensure_injury_record(player: Player, fpl_player: dict) -> None:
    status = fpl_player.get("status") or "a"
    news = (fpl_player.get("news") or "").strip()
    if status != "i" or "injury" not in news.lower():
        return

    injury_date = _parse_news_date(fpl_player.get("news_added")) or timezone.localdate()
    body_part = _infer_body_part(news)
    severity = _infer_severity(status, fpl_player.get("chance_of_playing_this_round"))
    days_out_map = {
        InjuryRecord.Severity.MINOR: 7,
        InjuryRecord.Severity.MODERATE: 21,
        InjuryRecord.Severity.SEVERE: 45,
    }
    days_out = days_out_map[severity]
    injury_type = news.split(" - ")[0][:80] if news else "Травма"

    exists = InjuryRecord.objects.filter(
        player=player,
        injury_date=injury_date,
        body_part=body_part,
    ).exists()
    if exists:
        return

    InjuryRecord.objects.create(
        player=player,
        injury_date=injury_date,
        body_part=body_part,
        injury_type=injury_type,
        severity=severity,
        days_out=days_out,
        matches_missed=max(1, days_out // 7),
        recovery_date=injury_date + timedelta(days=days_out),
        treatment="Программа восстановления клуба",
        description=news[:500],
    )


def sync_fpl_data(force: bool = False) -> DataSyncLog:
    lock_key = "apl_fpl_sync_lock"
    if not force and cache.get(lock_key):
        latest = DataSyncLog.objects.filter(source="fpl", status=DataSyncLog.Status.SUCCESS).first()
        if latest:
            return latest

    cache.set(lock_key, True, timeout=getattr(settings, "FPL_SYNC_LOCK_SECONDS", 600))
    try:
        payload = fetch_fpl_payload()
        teams = payload.get("teams") or []
        elements = [item for item in (payload.get("elements") or []) if not item.get("removed")]

        with transaction.atomic():
            clubs_by_fpl_id = _upsert_clubs(teams)
            Player.objects.filter(external_id__isnull=True).exclude(
                data_source=Player.DataSource.MANUAL
            ).delete()

            seen_ids: set[int] = set()
            synced_players = 0

            for fpl_player in elements:
                club = clubs_by_fpl_id.get(fpl_player["team"])
                if not club:
                    continue

                previous = Player.objects.filter(external_id=fpl_player["id"]).first()
                previous_minutes = previous.season_minutes if previous else 0
                previous_injuries = previous.season_injuries if previous else 0

                season_injuries, career_injuries, last_injury_date, is_available = 0, 0, None, (
                    fpl_player.get("status") == "a"
                )
                season_minutes = min(4000, int(fpl_player.get("minutes") or 0))
                market_value = Decimal(str(max(1, int(fpl_player.get("now_cost") or 50)) / 10)).quantize(
                    Decimal("0.01")
                )

                player, _ = Player.objects.update_or_create(
                    external_id=fpl_player["id"],
                    defaults={
                        "club": club,
                        "data_source": Player.DataSource.FPL,
                        "last_synced_at": timezone.now(),
                        "full_name": _player_full_name(fpl_player),
                        "position": POSITION_MAP.get(fpl_player.get("element_type"), Player.Position.MIDFIELDER),
                        "age": _calc_age(_parse_birth_date(fpl_player.get("birth_date"))),
                        "nationality": "England",
                        "dominant_foot": "Right",
                        "market_value": market_value,
                        "season_minutes": season_minutes,
                        "last_injury_date": last_injury_date,
                        "season_injuries": season_injuries,
                        "career_injuries": career_injuries,
                        "minutes_last_5": min(season_minutes, 450),
                        "previous_injuries": career_injuries,
                        "injury_history_score": min(100, career_injuries * 8),
                        "is_available": is_available,
                    },
                )
                seen_ids.add(fpl_player["id"])
                _ensure_assessment(player, previous_minutes, previous_injuries)
                synced_players += 1

            Player.objects.filter(data_source=Player.DataSource.FPL).exclude(
                external_id__in=seen_ids
            ).delete()
            Club.objects.filter(external_id__isnull=True, players__isnull=True).delete()

            log = DataSyncLog.objects.create(
                source="fpl",
                status=DataSyncLog.Status.SUCCESS,
                players_synced=synced_players,
                clubs_synced=len(clubs_by_fpl_id),
                message=f"Загружено {synced_players} игроков из Fantasy Premier League.",
            )
            return log
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError) as exc:
        logger.exception("FPL sync failed")
        return DataSyncLog.objects.create(
            source="fpl",
            status=DataSyncLog.Status.FAILED,
            message=str(exc),
        )
    finally:
        cache.delete(lock_key)


def latest_sync_log() -> DataSyncLog | None:
    return DataSyncLog.objects.filter(source="fpl").first()


def sync_is_stale() -> bool:
    latest = DataSyncLog.objects.filter(
        source="fpl",
        status=DataSyncLog.Status.SUCCESS,
    ).first()
    if not latest:
        return True
    interval = timedelta(hours=getattr(settings, "FPL_SYNC_INTERVAL_HOURS", 12))
    return timezone.now() - latest.synced_at > interval


def ensure_data_synced(force: bool = False) -> DataSyncLog | None:
    if force or sync_is_stale() or Player.objects.filter(data_source=Player.DataSource.FPL).count() == 0:
        return sync_fpl_data(force=force)
    return latest_sync_log()
