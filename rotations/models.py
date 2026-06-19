from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils import timezone


class Club(models.Model):
    external_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID from external football API (FPL).",
    )
    name = models.CharField("club name", max_length=120, unique=True)
    short_name = models.CharField("short name", max_length=12, unique=True)
    city = models.CharField(max_length=80)
    stadium = models.CharField(max_length=120)
    medical_budget = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text="Annual medical and recovery budget in million GBP.",
    )

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Player(models.Model):
    class Position(models.TextChoices):
        GOALKEEPER = "GK", "Вратарь"
        DEFENDER = "DF", "Защитник"
        MIDFIELDER = "MF", "Полузащитник"
        FORWARD = "FW", "Нападающий"

    class DataSource(models.TextChoices):
        MANUAL = "manual", "Manual"
        FPL = "fpl", "Fantasy Premier League"

    club = models.ForeignKey(
        Club,
        on_delete=models.CASCADE,
        related_name="players",
    )
    external_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        unique=True,
        help_text="ID from external football API (FPL).",
    )
    data_source = models.CharField(
        max_length=20,
        choices=DataSource.choices,
        blank=True,
        default="",
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    transfermarkt_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Player ID on Transfermarkt.",
    )
    full_name = models.CharField(max_length=120)
    position = models.CharField(max_length=2, choices=Position.choices)
    age = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(16), MaxValueValidator(45)]
    )
    nationality = models.CharField(max_length=80)
    dominant_foot = models.CharField(max_length=20, default="Right")
    market_value = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        help_text="Market value in million GBP.",
    )
    season_minutes = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(4000)],
        help_text="Minutes played during the current season.",
    )
    last_injury_date = models.DateField(null=True, blank=True)
    season_injuries = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
    )
    career_injuries = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(60)],
    )
    minutes_last_5 = models.PositiveSmallIntegerField(default=0)
    previous_injuries = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(20)],
        help_text="Number of previous injuries recorded for this player.",
    )
    injury_history_score = models.PositiveSmallIntegerField(
        default=20,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Legacy historical factor from 0 to 100.",
    )
    is_available = models.BooleanField(default=True)

    class Meta:
        ordering = ["club__name", "full_name"]
        unique_together = ["club", "full_name"]

    def __str__(self):
        return f"{self.full_name} ({self.club.short_name})"

    def get_absolute_url(self):
        return reverse("player_detail", kwargs={"pk": self.pk})

    @property
    def latest_assessment(self):
        return self.assessments.order_by("-date", "-created_at").first()

    @property
    def current_risk_score(self):
        assessment = self.latest_assessment
        return assessment.risk_score if assessment else None

    @property
    def current_risk_level(self):
        assessment = self.latest_assessment
        return assessment.risk_level if assessment else "unknown"


class TrainingLoad(models.Model):
    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="training_loads",
    )
    date = models.DateField()
    minutes_played = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(130)]
    )
    distance_km = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(16)],
    )
    sprint_count = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(80)]
    )
    accelerations = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(120)]
    )
    perceived_exertion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="RPE scale from 1 to 10.",
    )
    sleep_hours = models.DecimalField(
        max_digits=4,
        decimal_places=1,
        validators=[MinValueValidator(0), MaxValueValidator(14)],
    )
    soreness_level = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(10)]
    )

    class Meta:
        ordering = ["-date"]
        unique_together = ["player", "date"]

    def __str__(self):
        return f"{self.player.full_name}: {self.date}"

    @property
    def load_score(self):
        minutes_component = self.minutes_played / 130 * 30
        sprint_component = self.sprint_count / 80 * 20
        rpe_component = self.perceived_exertion / 10 * 25
        soreness_component = self.soreness_level / 10 * 25
        return round(minutes_component + sprint_component + rpe_component + soreness_component, 1)


class InjuryAssessment(models.Model):
    class RiskLevel(models.TextChoices):
        LOW = "low", "Низкий"
        MEDIUM = "medium", "Средний"
        HIGH = "high", "Высокий"

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="assessments",
    )
    date = models.DateField()
    season_minutes_at_assessment = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Player season minutes at the time of this assessment.",
    )
    last_injury_date_at_assessment = models.DateField(
        null=True,
        blank=True,
        help_text="Player last injury date at the time of this assessment.",
    )
    season_injuries_at_assessment = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Player season injuries at the time of this assessment.",
    )
    career_injuries_at_assessment = models.PositiveSmallIntegerField(
        null=True,
        blank=True,
        help_text="Player career injuries at the time of this assessment.",
    )
    muscle_fatigue = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    joint_stability = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    previous_injury_factor = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    recovery_score = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)]
    )
    risk_score = models.DecimalField(max_digits=5, decimal_places=2, editable=False)
    risk_level = models.CharField(
        max_length=10,
        choices=RiskLevel.choices,
        editable=False,
    )
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date", "-created_at"]
        unique_together = ["player", "date"]

    def __str__(self):
        return f"{self.player.full_name}: {self.risk_score}%"

    def calculate_risk_score(self):
        from .risk_engine import calculate_player_risk

        result = calculate_player_risk(
            self.player,
            on_date=self.date,
            season_minutes=self.season_minutes_at_assessment,
            season_injuries=self.season_injuries_at_assessment,
            career_injuries=self.career_injuries_at_assessment,
            last_injury_date=self.last_injury_date_at_assessment,
            assessment=self,
        )
        return result["total"]

    @staticmethod
    def level_for_score(score):
        if score >= 65:
            return InjuryAssessment.RiskLevel.HIGH
        if score >= 35:
            return InjuryAssessment.RiskLevel.MEDIUM
        return InjuryAssessment.RiskLevel.LOW

    def save(self, *args, **kwargs):
        if self._state.adding:
            if self.season_minutes_at_assessment is None:
                self.season_minutes_at_assessment = self.player.season_minutes
            if self.last_injury_date_at_assessment is None:
                self.last_injury_date_at_assessment = self.player.last_injury_date
            if self.season_injuries_at_assessment is None:
                self.season_injuries_at_assessment = self.player.season_injuries
            if self.career_injuries_at_assessment is None:
                self.career_injuries_at_assessment = self.player.career_injuries
        self.risk_score = self.calculate_risk_score()
        self.risk_level = self.level_for_score(self.risk_score)
        super().save(*args, **kwargs)


class InjuryRecord(models.Model):
    class BodyPart(models.TextChoices):
        KNEE = "knee", "Колено"
        HAMSTRING = "hamstring", "Задняя поверхность бедра"
        ANKLE = "ankle", "Голеностоп"
        GROIN = "groin", "Пах"
        CALF = "calf", "Икра"
        SHOULDER = "shoulder", "Плечо"
        BACK = "back", "Спина"
        HEAD = "head", "Голова"
        OTHER = "other", "Другое"

    class Severity(models.TextChoices):
        MINOR = "minor", "Лёгкая"
        MODERATE = "moderate", "Средняя"
        SEVERE = "severe", "Тяжёлая"

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="injury_records",
    )
    injury_date = models.DateField()
    body_part = models.CharField(max_length=20, choices=BodyPart.choices)
    injury_type = models.CharField(max_length=80)
    severity = models.CharField(max_length=10, choices=Severity.choices)
    days_out = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(365)],
    )
    matches_missed = models.PositiveSmallIntegerField(
        default=0,
        validators=[MinValueValidator(0), MaxValueValidator(50)],
    )
    recovery_date = models.DateField(null=True, blank=True)
    treatment = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-injury_date"]

    def __str__(self):
        return f"{self.player.full_name}: {self.get_body_part_display()} ({self.injury_date})"

    @property
    def is_recovered(self):
        if self.recovery_date:
            return self.recovery_date <= timezone.localdate()
        return self.days_out == 0


class DataSyncLog(models.Model):
    class Status(models.TextChoices):
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"

    source = models.CharField(max_length=40, default="fpl")
    synced_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=Status.choices)
    players_synced = models.PositiveIntegerField(default=0)
    clubs_synced = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-synced_at"]

    def __str__(self):
        return f"{self.source} @ {self.synced_at:%Y-%m-%d %H:%M}"


class RotationPlan(models.Model):
    class Recommendation(models.TextChoices):
        START = "start", "Start"
        LIMITED = "limited", "Limited minutes"
        REST = "rest", "Rest"
        MEDICAL_REVIEW = "medical_review", "Medical review"

    player = models.ForeignKey(
        Player,
        on_delete=models.CASCADE,
        related_name="rotation_plans",
    )
    assessment = models.ForeignKey(
        InjuryAssessment,
        on_delete=models.SET_NULL,
        related_name="rotation_plans",
        null=True,
        blank=True,
    )
    match_date = models.DateField()
    opponent = models.CharField(max_length=120)
    planned_minutes = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(120)]
    )
    recommendation = models.CharField(max_length=20, choices=Recommendation.choices)
    rationale = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["match_date", "player__club__name", "player__full_name"]

    def __str__(self):
        return f"{self.player.full_name} vs {self.opponent}: {self.get_recommendation_display()}"
