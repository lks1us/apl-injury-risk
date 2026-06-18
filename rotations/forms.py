from django import forms
from django.utils import timezone

from .models import InjuryAssessment, Player, RotationPlan, TrainingLoad


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs.setdefault("class", css_class)


class PlayerForm(BootstrapModelForm):
    class Meta:
        model = Player
        fields = [
            "club",
            "full_name",
            "position",
            "season_minutes",
            "last_injury_date",
            "season_injuries",
            "career_injuries",
        ]
        widgets = {"last_injury_date": forms.DateInput(attrs={"type": "date"})}

    def clean_season_minutes(self):
        minutes = self.cleaned_data["season_minutes"]
        if minutes > 4000:
            raise forms.ValidationError("Season minutes cannot exceed 4000.")
        return minutes

    def clean_last_injury_date(self):
        date = self.cleaned_data["last_injury_date"]
        if date and date > timezone.localdate():
            raise forms.ValidationError("Last injury date cannot be in the future.")
        return date

    def save(self, commit=True):
        player = super().save(commit=False)
        player.age = player.age or 24
        player.nationality = player.nationality or "Unknown"
        player.dominant_foot = player.dominant_foot or "Right"
        player.market_value = player.market_value or 0
        player.minutes_last_5 = min(player.season_minutes, 450)
        player.previous_injuries = player.career_injuries
        player.injury_history_score = min(100, player.career_injuries * 10)
        player.is_available = player.season_injuries < 3
        if commit:
            player.save()
        return player


class TrainingLoadForm(BootstrapModelForm):
    class Meta:
        model = TrainingLoad
        fields = [
            "date",
            "minutes_played",
            "distance_km",
            "sprint_count",
            "accelerations",
            "perceived_exertion",
            "sleep_hours",
            "soreness_level",
        ]
        widgets = {"date": forms.DateInput(attrs={"type": "date"})}

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date > timezone.localdate():
            raise forms.ValidationError("Training load date cannot be in the future.")
        return date


class InjuryAssessmentForm(BootstrapModelForm):
    class Meta:
        model = InjuryAssessment
        fields = [
            "date",
            "notes",
        ]
        widgets = {
            "date": forms.DateInput(attrs={"type": "date"}),
            "notes": forms.Textarea(attrs={"rows": 4}),
        }

    def clean_date(self):
        date = self.cleaned_data["date"]
        if date > timezone.localdate():
            raise forms.ValidationError("Assessment date cannot be in the future.")
        return date


class RotationPlanForm(BootstrapModelForm):
    class Meta:
        model = RotationPlan
        fields = [
            "assessment",
            "match_date",
            "opponent",
            "planned_minutes",
            "recommendation",
            "rationale",
        ]
        widgets = {
            "match_date": forms.DateInput(attrs={"type": "date"}),
            "rationale": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, **kwargs):
        self.player = kwargs.pop("player", None)
        super().__init__(*args, **kwargs)
        if self.player:
            self.fields["assessment"].queryset = self.player.assessments.all()

    def clean(self):
        cleaned = super().clean()
        recommendation = cleaned.get("recommendation")
        planned_minutes = cleaned.get("planned_minutes")
        if recommendation == RotationPlan.Recommendation.REST and planned_minutes:
            raise forms.ValidationError("Rest recommendation should use 0 planned minutes.")
        if recommendation == RotationPlan.Recommendation.START and planned_minutes is not None and planned_minutes < 60:
            raise forms.ValidationError("Start recommendation should plan at least 60 minutes.")
        return cleaned
