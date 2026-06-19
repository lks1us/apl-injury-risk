from datetime import timedelta

from django import forms
from django.utils import timezone

from .models import InjuryAssessment, InjuryRecord, Player, RotationPlan, TrainingLoad

SEVERITY_DAYS_OUT = {
    InjuryRecord.Severity.MINOR: 7,
    InjuryRecord.Severity.MODERATE: 21,
    InjuryRecord.Severity.SEVERE: 45,
}


class BootstrapModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            css_class = "form-select" if isinstance(field.widget, forms.Select) else "form-control"
            if isinstance(field.widget, forms.CheckboxInput):
                css_class = "form-check-input"
            field.widget.attrs.setdefault("class", css_class)


class PlayerForm(BootstrapModelForm):
    injury_body_part = forms.ChoiceField(
        choices=InjuryRecord.BodyPart.choices,
        required=False,
        label="Зона травмы",
    )
    injury_severity = forms.ChoiceField(
        choices=InjuryRecord.Severity.choices,
        required=False,
        label="Тяжесть травмы",
    )

    class Meta:
        model = Player
        fields = [
            "club",
            "full_name",
            "position",
            "season_minutes",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["club"].label = "Клуб"
        self.fields["full_name"].label = "Имя игрока"
        self.fields["position"].label = "Позиция"
        self.fields["season_minutes"].label = "Минуты за сезон"
        self.fields["injury_body_part"].choices = [("", "— не указана —")] + list(
            InjuryRecord.BodyPart.choices
        )
        self.fields["injury_severity"].choices = [("", "— не указана —")] + list(
            InjuryRecord.Severity.choices
        )
        self.order_fields(
            [
                "club",
                "full_name",
                "position",
                "season_minutes",
                "injury_body_part",
                "injury_severity",
            ]
        )

    def clean_season_minutes(self):
        minutes = self.cleaned_data["season_minutes"]
        if minutes > 4000:
            raise forms.ValidationError("Минут за сезон не может быть больше 4000.")
        return minutes

    def clean(self):
        cleaned = super().clean()
        severity = cleaned.get("injury_severity")
        body_part = cleaned.get("injury_body_part")
        if severity and not body_part:
            self.add_error("injury_body_part", "Укажите зону травмы.")
        if body_part and not severity:
            self.add_error("injury_severity", "Укажите тяжесть травмы.")
        return cleaned

    def save(self, commit=True):
        player = super().save(commit=False)
        player.data_source = Player.DataSource.MANUAL
        player.age = player.age or 24
        player.nationality = player.nationality or "Unknown"
        player.dominant_foot = player.dominant_foot or "Right"
        player.market_value = player.market_value or 0
        player.minutes_last_5 = min(player.season_minutes, 450)

        severity = self.cleaned_data.get("injury_severity")
        body_part = self.cleaned_data.get("injury_body_part")
        if severity and body_part:
            player.last_injury_date = timezone.localdate()
            player.season_injuries = 1
            player.career_injuries = 1
        else:
            player.last_injury_date = None
            player.season_injuries = 0
            player.career_injuries = 0

        player.previous_injuries = player.career_injuries
        player.injury_history_score = min(100, player.career_injuries * 10)
        player.is_available = player.season_injuries < 3
        if commit:
            player.save()
        return player

    def create_injury_record(self, player):
        severity = self.cleaned_data.get("injury_severity")
        body_part = self.cleaned_data.get("injury_body_part")
        if not severity or not body_part:
            return None

        injury_date = timezone.localdate()
        days_out = SEVERITY_DAYS_OUT[severity]
        body_label = dict(InjuryRecord.BodyPart.choices)[body_part]
        severity_label = dict(InjuryRecord.Severity.choices)[severity]
        return InjuryRecord.objects.create(
            player=player,
            injury_date=injury_date,
            body_part=body_part,
            injury_type=f"{body_label}, {severity_label}",
            severity=severity,
            days_out=days_out,
            matches_missed=max(1, days_out // 7),
            recovery_date=injury_date + timedelta(days=days_out),
            treatment="",
            description=f"Зона: {body_label}. Тяжесть: {severity_label}.",
        )


class InjuryUpdateForm(BootstrapModelForm):
    class Meta:
        model = InjuryRecord
        fields = ["injury_date", "body_part", "severity"]
        widgets = {"injury_date": forms.DateInput(attrs={"type": "date"})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["injury_date"].label = "Дата травмы"
        self.fields["body_part"].label = "Зона травмы"
        self.fields["severity"].label = "Тяжесть травмы"
        if not self.instance.pk and not self.is_bound:
            self.initial.setdefault("injury_date", timezone.localdate())

    def clean_injury_date(self):
        injury_date = self.cleaned_data["injury_date"]
        if injury_date > timezone.localdate():
            raise forms.ValidationError("Дата травмы не может быть в будущем.")
        return injury_date

    def save_for_player(self, player):
        injury_date = self.cleaned_data["injury_date"]
        body_part = self.cleaned_data["body_part"]
        severity = self.cleaned_data["severity"]
        days_out = SEVERITY_DAYS_OUT[severity]
        body_label = dict(InjuryRecord.BodyPart.choices)[body_part]
        severity_label = dict(InjuryRecord.Severity.choices)[severity]

        latest = player.injury_records.order_by("-injury_date", "-pk").first()
        if latest:
            latest.injury_date = injury_date
            latest.body_part = body_part
            latest.severity = severity
            latest.days_out = days_out
            latest.matches_missed = max(1, days_out // 7)
            latest.recovery_date = injury_date + timedelta(days=days_out)
            latest.injury_type = f"{body_label}, {severity_label}"
            latest.description = f"Зона: {body_label}. Тяжесть: {severity_label}."
            latest.save()
            injury = latest
        else:
            injury = InjuryRecord.objects.create(
                player=player,
                injury_date=injury_date,
                body_part=body_part,
                severity=severity,
                days_out=days_out,
                matches_missed=max(1, days_out // 7),
                recovery_date=injury_date + timedelta(days=days_out),
                injury_type=f"{body_label}, {severity_label}",
                description=f"Зона: {body_label}. Тяжесть: {severity_label}.",
            )

        player.last_injury_date = injury_date
        player.season_injuries = max(player.season_injuries, 1)
        player.career_injuries = max(player.career_injuries, 1)
        player.previous_injuries = player.career_injuries
        player.injury_history_score = min(100, player.career_injuries * 10)
        player.is_available = severity == InjuryRecord.Severity.MINOR and days_out <= 7
        player.save(
            update_fields=[
                "last_injury_date",
                "season_injuries",
                "career_injuries",
                "previous_injuries",
                "injury_history_score",
                "is_available",
            ]
        )
        return injury


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
