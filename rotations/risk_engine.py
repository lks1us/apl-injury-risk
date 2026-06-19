"""Единая модель расчёта риска травмы."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date

from django.utils import timezone

from .models import InjuryAssessment, InjuryRecord, Player

SEASON_MINUTES_CAP = 3420
RECENT_MINUTES_CAP = 450

POSITION_FACTOR = {
    Player.Position.GOALKEEPER: 0.88,
    Player.Position.DEFENDER: 0.94,
    Player.Position.MIDFIELDER: 1.0,
    Player.Position.FORWARD: 1.07,
}

SEVERITY_ACTIVE_BONUS = {
    InjuryRecord.Severity.MINOR: 4,
    InjuryRecord.Severity.MODERATE: 8,
    InjuryRecord.Severity.SEVERE: 12,
}


@dataclass
class RiskComponent:
    label: str
    value: float
    max: float
    hint: str


def _age_factor(age: int) -> float:
    if age <= 21:
        return 1.04
    if age <= 28:
        return 1.0
    if age <= 32:
        return 1.05
    return min(1.18, 1.05 + (age - 32) * 0.025)


def _season_workload_score(minutes: int) -> float:
    if minutes <= 0:
        return 0.0
    ratio = min(1.0, minutes / SEASON_MINUTES_CAP)
    base = 20 * (ratio**1.25)
    if minutes > 2700:
        overload = min(4.0, (minutes - 2700) / (SEASON_MINUTES_CAP - 2700) * 4)
        base += overload
    return min(24.0, base)


def _recent_workload_score(minutes_last_5: int) -> float:
    ratio = min(1.0, minutes_last_5 / RECENT_MINUTES_CAP)
    return round(14 * ratio, 2)


def _season_injury_score(season_injuries: int) -> float:
    if season_injuries <= 0:
        return 0.0
    return min(18.0, season_injuries * 5 + math.sqrt(season_injuries) * 2)


def _career_injury_score(career_injuries: int) -> float:
    if career_injuries <= 0:
        return 0.0
    return min(14.0, math.log2(career_injuries + 1) * 4.2)


def _recency_score(last_injury_date: date | None, on_date: date) -> float:
    if not last_injury_date:
        return 0.0
    days_since = (on_date - last_injury_date).days
    if days_since < 0 or days_since > 365:
        return 0.0
    return round(18 * math.exp(-days_since / 42), 2)


def _availability_score(player: Player) -> tuple[float, str]:
    if player.is_available:
        return 0.0, "игрок доступен"
    return 10.0, "игрок недоступен / восстанавливается"


def _active_injury_score(player: Player, on_date: date) -> tuple[float, str]:
    active = (
        player.injury_records.filter(injury_date__lte=on_date)
        .order_by("-injury_date")
        .first()
    )
    if not active:
        return 0.0, "нет активной записи о травме"

    if active.recovery_date and active.recovery_date < on_date:
        return 0.0, "последняя травма уже закрыта"

    bonus = SEVERITY_ACTIVE_BONUS.get(active.severity, 6)
    return float(bonus), f"{active.get_severity_display()} ({active.get_body_part_display()})"


def _assessment_modifier(assessment: InjuryAssessment | None) -> float:
    if not assessment:
        return 0.0
    fatigue = assessment.muscle_fatigue / 100 * 4
    instability = (100 - assessment.joint_stability) / 100 * 3
    poor_recovery = (100 - assessment.recovery_score) / 100 * 3
    return min(8.0, fatigue + instability + poor_recovery)


def calculate_player_risk(
    player: Player,
    on_date: date | None = None,
    *,
    season_minutes: int | None = None,
    season_injuries: int | None = None,
    career_injuries: int | None = None,
    last_injury_date: date | None = None,
    assessment: InjuryAssessment | None = None,
) -> dict:
    reference = on_date or timezone.localdate()
    minutes = season_minutes if season_minutes is not None else player.season_minutes
    season_inj = season_injuries if season_injuries is not None else player.season_injuries
    career_inj = career_injuries if career_injuries is not None else player.career_injuries
    injury_date = last_injury_date if last_injury_date is not None else player.last_injury_date

    workload = round(_season_workload_score(minutes), 2)
    recent = _recent_workload_score(player.minutes_last_5)
    season_injury = round(_season_injury_score(season_inj), 2)
    career_injury = round(_career_injury_score(career_inj), 2)
    recency = _recency_score(injury_date, reference)
    availability, availability_hint = _availability_score(player)
    active_injury, active_hint = _active_injury_score(player, reference)
    assessment_extra = round(_assessment_modifier(assessment), 2)

    components = [
        RiskComponent("Нагрузка за сезон", workload, 24, f"{minutes} мин"),
        RiskComponent("Нагрузка за 5 матчей", recent, 14, f"{player.minutes_last_5} мин"),
        RiskComponent("Травмы в сезоне", season_injury, 18, f"{season_inj} случаев"),
        RiskComponent("История травм", career_injury, 14, f"{career_inj} за карьеру"),
        RiskComponent("Недавняя травма", recency, 18, _recency_hint(injury_date, reference)),
        RiskComponent("Текущий статус", availability, 10, availability_hint),
        RiskComponent("Активная травма", active_injury, 12, active_hint),
    ]
    if assessment_extra:
        components.append(
            RiskComponent("Медицинские показатели", assessment_extra, 8, "усталость и восстановление")
        )

    raw_total = sum(item.value for item in components)
    position_factor = POSITION_FACTOR.get(player.position, 1.0)
    age_factor = _age_factor(player.age)
    total = round(min(100.0, raw_total * position_factor * age_factor), 2)

    return {
        "total": total,
        "level": InjuryAssessment.level_for_score(total),
        "components": [
            {
                "label": item.label,
                "value": item.value,
                "max": item.max,
                "hint": item.hint,
            }
            for item in components
        ],
    }


def _recency_hint(last_injury_date: date | None, on_date: date) -> str:
    if not last_injury_date:
        return "нет данных"
    days_since = (on_date - last_injury_date).days
    return f"{days_since} дн. назад"
