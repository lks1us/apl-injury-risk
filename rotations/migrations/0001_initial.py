# Generated for the APL Risk Rotation educational project.
from django.db import migrations, models
import django.core.validators
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Club",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=120, unique=True, verbose_name="club name")),
                ("short_name", models.CharField(max_length=12, unique=True, verbose_name="short name")),
                ("city", models.CharField(max_length=80)),
                ("stadium", models.CharField(max_length=120)),
                (
                    "medical_budget",
                    models.DecimalField(
                        decimal_places=2,
                        help_text="Annual medical and recovery budget in million GBP.",
                        max_digits=10,
                    ),
                ),
            ],
            options={"ordering": ["name"]},
        ),
        migrations.CreateModel(
            name="Player",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("full_name", models.CharField(max_length=120)),
                (
                    "position",
                    models.CharField(
                        choices=[
                            ("GK", "Goalkeeper"),
                            ("DF", "Defender"),
                            ("MF", "Midfielder"),
                            ("FW", "Forward"),
                        ],
                        max_length=2,
                    ),
                ),
                (
                    "age",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(16),
                            django.core.validators.MaxValueValidator(45),
                        ]
                    ),
                ),
                ("nationality", models.CharField(max_length=80)),
                ("dominant_foot", models.CharField(default="Right", max_length=20)),
                (
                    "market_value",
                    models.DecimalField(decimal_places=2, help_text="Market value in million GBP.", max_digits=8),
                ),
                ("minutes_last_5", models.PositiveSmallIntegerField(default=0)),
                (
                    "injury_history_score",
                    models.PositiveSmallIntegerField(
                        default=20,
                        help_text="Historical injury factor from 0 to 100.",
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ],
                    ),
                ),
                ("is_available", models.BooleanField(default=True)),
                (
                    "club",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="players",
                        to="rotations.club",
                    ),
                ),
            ],
            options={"ordering": ["club__name", "full_name"], "unique_together": {("club", "full_name")}},
        ),
        migrations.CreateModel(
            name="InjuryAssessment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                (
                    "muscle_fatigue",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                (
                    "joint_stability",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                (
                    "previous_injury_factor",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                (
                    "recovery_score",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(100),
                        ]
                    ),
                ),
                ("risk_score", models.DecimalField(decimal_places=2, editable=False, max_digits=5)),
                (
                    "risk_level",
                    models.CharField(
                        choices=[("low", "Low"), ("medium", "Medium"), ("high", "High")],
                        editable=False,
                        max_length=10,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="assessments",
                        to="rotations.player",
                    ),
                ),
            ],
            options={"ordering": ["-date", "-created_at"], "unique_together": {("player", "date")}},
        ),
        migrations.CreateModel(
            name="TrainingLoad",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("date", models.DateField()),
                (
                    "minutes_played",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(130),
                        ]
                    ),
                ),
                (
                    "distance_km",
                    models.DecimalField(
                        decimal_places=2,
                        max_digits=5,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(16),
                        ],
                    ),
                ),
                (
                    "sprint_count",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(80),
                        ]
                    ),
                ),
                (
                    "accelerations",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(120),
                        ]
                    ),
                ),
                (
                    "perceived_exertion",
                    models.PositiveSmallIntegerField(
                        help_text="RPE scale from 1 to 10.",
                        validators=[
                            django.core.validators.MinValueValidator(1),
                            django.core.validators.MaxValueValidator(10),
                        ],
                    ),
                ),
                (
                    "sleep_hours",
                    models.DecimalField(
                        decimal_places=1,
                        max_digits=4,
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(14),
                        ],
                    ),
                ),
                (
                    "soreness_level",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(10),
                        ]
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="training_loads",
                        to="rotations.player",
                    ),
                ),
            ],
            options={"ordering": ["-date"], "unique_together": {("player", "date")}},
        ),
        migrations.CreateModel(
            name="RotationPlan",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("match_date", models.DateField()),
                ("opponent", models.CharField(max_length=120)),
                (
                    "planned_minutes",
                    models.PositiveSmallIntegerField(
                        validators=[
                            django.core.validators.MinValueValidator(0),
                            django.core.validators.MaxValueValidator(120),
                        ]
                    ),
                ),
                (
                    "recommendation",
                    models.CharField(
                        choices=[
                            ("start", "Start"),
                            ("limited", "Limited minutes"),
                            ("rest", "Rest"),
                            ("medical_review", "Medical review"),
                        ],
                        max_length=20,
                    ),
                ),
                ("rationale", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "assessment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="rotation_plans",
                        to="rotations.injuryassessment",
                    ),
                ),
                (
                    "player",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="rotation_plans",
                        to="rotations.player",
                    ),
                ),
            ],
            options={"ordering": ["match_date", "player__club__name", "player__full_name"]},
        ),
    ]
