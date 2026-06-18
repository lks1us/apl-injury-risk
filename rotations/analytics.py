from datetime import timedelta

import pandas as pd
from django.db.models import Avg, Count, Q
from django.utils import timezone

from .models import InjuryAssessment, Player, RotationPlan, TrainingLoad


def recent_training_load_frame(player, days=21):
    start_date = timezone.localdate() - timedelta(days=days)
    rows = TrainingLoad.objects.filter(player=player, date__gte=start_date).values(
        "date",
        "minutes_played",
        "distance_km",
        "sprint_count",
        "accelerations",
        "perceived_exertion",
        "sleep_hours",
        "soreness_level",
    )
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    frame["load_score"] = (
        frame["minutes_played"] / 130 * 30
        + frame["sprint_count"] / 80 * 20
        + frame["perceived_exertion"] / 10 * 25
        + frame["soreness_level"] / 10 * 25
    ).round(1)
    return frame.sort_values("date")


def player_risk_projection(player):
    frame = recent_training_load_frame(player)
    assessment = player.latest_assessment

    if frame.empty:
        avg_load = 0
        avg_sleep = 8
        sprint_pressure = 0
    else:
        avg_load = frame["load_score"].mean()
        avg_sleep = frame["sleep_hours"].mean()
        sprint_pressure = min(100, frame["sprint_count"].sum() / 3)

    minutes_component = min(45, player.season_minutes / 3420 * 45)
    season_injury_component = min(30, player.season_injuries * 10)
    career_injury_component = min(20, player.career_injuries * 3)
    recency_component = 0
    if player.last_injury_date:
        days_since_injury = (timezone.localdate() - player.last_injury_date).days
        if days_since_injury <= 30:
            recency_component = 5
        elif days_since_injury <= 90:
            recency_component = 3
        elif days_since_injury <= 180:
            recency_component = 1
    projected = round(
        min(100, minutes_component + season_injury_component + career_injury_component + recency_component),
        1,
    )

    if projected >= 70:
        recommendation = RotationPlan.Recommendation.MEDICAL_REVIEW
        minutes = 0
    elif projected >= 58:
        recommendation = RotationPlan.Recommendation.REST
        minutes = 0
    elif projected >= 42:
        recommendation = RotationPlan.Recommendation.LIMITED
        minutes = 45
    else:
        recommendation = RotationPlan.Recommendation.START
        minutes = 75

    return {
        "projected_score": projected,
        "avg_load": round(float(avg_load), 1),
        "avg_sleep": round(float(avg_sleep), 1),
        "recommendation": recommendation,
        "recommendation_label": RotationPlan.Recommendation(recommendation).label,
        "planned_minutes": minutes,
    }


def assessment_trend(player):
    rows = player.assessments.order_by("date").values("date", "risk_score")
    frame = pd.DataFrame.from_records(rows)
    if frame.empty:
        return {"labels": [], "scores": [], "rolling": []}
    frame["date"] = pd.to_datetime(frame["date"])
    frame["risk_score"] = frame["risk_score"].astype(float)
    frame["rolling"] = frame["risk_score"].rolling(window=3, min_periods=1).mean().round(1)
    return {
        "labels": [value.strftime("%d.%m") for value in frame["date"]],
        "scores": frame["risk_score"].round(1).tolist(),
        "rolling": frame["rolling"].tolist(),
    }


def training_load_chart(player):
    frame = recent_training_load_frame(player, days=35)
    if frame.empty:
        return {"labels": [], "loads": [], "sleep": []}
    return {
        "labels": [value.strftime("%d.%m") for value in frame["date"]],
        "loads": frame["load_score"].round(1).tolist(),
        "sleep": frame["sleep_hours"].astype(float).round(1).tolist(),
    }


def dashboard_summary():
    players = Player.objects.select_related("club").annotate(
        avg_risk=Avg("assessments__risk_score"),
        load_records=Count("training_loads"),
    )
    player_stats = list(players)
    player_count = len(player_stats)
    low_risk_count = sum(1 for player in player_stats if player.avg_risk is not None and float(player.avg_risk) < 35)
    medium_risk_count = sum(
        1
        for player in player_stats
        if player.avg_risk is not None and 35 <= float(player.avg_risk) < 65
    )
    high_risk_count = sum(1 for player in player_stats if player.avg_risk is not None and float(player.avg_risk) >= 65)
    assessments = InjuryAssessment.objects.all()
    club_rows = (
        Player.objects.values("club__short_name")
        .annotate(avg_risk=Avg("assessments__risk_score"), player_count=Count("id"))
        .order_by("club__short_name")
    )
    return {
        "player_count": player_count,
        "club_count": players.values("club").distinct().count(),
        "avg_risk": assessments.aggregate(avg=Avg("risk_score"))["avg"] or 0,
        "high_risk_count": high_risk_count,
        "low_risk_count": low_risk_count,
        "medium_risk_count": medium_risk_count,
        "low_risk_pct": round(low_risk_count / max(player_count, 1) * 100),
        "medium_risk_pct": round(medium_risk_count / max(player_count, 1) * 100),
        "high_risk_pct": round(high_risk_count / max(player_count, 1) * 100),
        "risk_distribution": {
            InjuryAssessment.RiskLevel.LOW: low_risk_count,
            InjuryAssessment.RiskLevel.MEDIUM: medium_risk_count,
            InjuryAssessment.RiskLevel.HIGH: high_risk_count,
        },
        "club_labels": [row["club__short_name"] for row in club_rows],
        "club_risks": [round(float(row["avg_risk"] or 0), 1) for row in club_rows],
        "club_risk_rows": [
            {
                "short_name": row["club__short_name"],
                "avg_risk": round(float(row["avg_risk"] or 0), 1),
                "avg_risk_width": round(float(row["avg_risk"] or 0)),
            }
            for row in club_rows
        ],
        "top_risk_players": players.filter(avg_risk__isnull=False).order_by("-avg_risk")[:12],
    }


def filtered_players(query_params):
    queryset = Player.objects.select_related("club").annotate(
        avg_risk=Avg("assessments__risk_score"),
        load_records=Count("training_loads"),
    )

    search = query_params.get("q", "").strip()
    if search:
        queryset = queryset.filter(
            Q(full_name__icontains=search)
            | Q(club__name__icontains=search)
            | Q(nationality__icontains=search)
        )

    club = query_params.get("club")
    if club:
        queryset = queryset.filter(club_id=club)

    position = query_params.get("position")
    if position:
        queryset = queryset.filter(position=position)

    availability = query_params.get("availability")
    if availability == "available":
        queryset = queryset.filter(is_available=True)
    elif availability == "unavailable":
        queryset = queryset.filter(is_available=False)

    risk = query_params.get("risk")
    if risk == "high":
        queryset = queryset.filter(avg_risk__gte=65)
    elif risk == "medium":
        queryset = queryset.filter(avg_risk__gte=35, avg_risk__lt=65)
    elif risk == "low":
        queryset = queryset.filter(avg_risk__lt=35)

    ordering_map = {
        "risk": "-avg_risk",
        "minutes": "-season_minutes",
        "age": "-age",
        "name": "full_name",
    }
    return queryset.order_by(ordering_map.get(query_params.get("sort"), "-avg_risk"))
