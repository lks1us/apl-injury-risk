from django.contrib import admin

from .models import Club, InjuryAssessment, Player, RotationPlan, TrainingLoad


@admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ("name", "short_name", "city", "stadium", "medical_budget")
    search_fields = ("name", "short_name", "city", "stadium")


@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "club",
        "position",
        "age",
        "season_minutes",
        "last_injury_date",
        "season_injuries",
        "career_injuries",
        "is_available",
    )
    list_filter = ("club", "position", "is_available")
    search_fields = ("full_name", "club__name", "nationality")


@admin.register(TrainingLoad)
class TrainingLoadAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "date",
        "minutes_played",
        "distance_km",
        "sprint_count",
        "perceived_exertion",
        "sleep_hours",
        "soreness_level",
    )
    list_filter = ("date", "player__club")
    search_fields = ("player__full_name", "player__club__name")


@admin.register(InjuryAssessment)
class InjuryAssessmentAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "date",
        "risk_score",
        "risk_level",
        "muscle_fatigue",
        "joint_stability",
        "recovery_score",
    )
    list_filter = ("risk_level", "date", "player__club")
    search_fields = ("player__full_name", "player__club__name", "notes")
    readonly_fields = ("risk_score", "risk_level", "created_at")


@admin.register(RotationPlan)
class RotationPlanAdmin(admin.ModelAdmin):
    list_display = (
        "player",
        "match_date",
        "opponent",
        "planned_minutes",
        "recommendation",
    )
    list_filter = ("recommendation", "match_date", "player__club")
    search_fields = ("player__full_name", "opponent", "rationale")
