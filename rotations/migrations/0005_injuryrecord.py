from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ("rotations", "0004_injuryassessment_snapshot_fields"),
    ]

    operations = [
        migrations.CreateModel(
            name="InjuryRecord",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("injury_date", models.DateField()),
                ("body_part", models.CharField(
                    choices=[
                        ("knee", "Колено"),
                        ("hamstring", "Задняя поверхность бедра"),
                        ("ankle", "Голеностоп"),
                        ("groin", "Пах"),
                        ("calf", "Икра"),
                        ("shoulder", "Плечо"),
                        ("back", "Спина"),
                        ("head", "Голова"),
                        ("other", "Другое"),
                    ],
                    max_length=20,
                )),
                ("injury_type", models.CharField(max_length=80)),
                ("severity", models.CharField(
                    choices=[
                        ("minor", "Лёгкая"),
                        ("moderate", "Средняя"),
                        ("severe", "Тяжёлая"),
                    ],
                    max_length=10,
                )),
                ("days_out", models.PositiveSmallIntegerField(
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(365),
                    ],
                )),
                ("matches_missed", models.PositiveSmallIntegerField(
                    default=0,
                    validators=[
                        django.core.validators.MinValueValidator(0),
                        django.core.validators.MaxValueValidator(50),
                    ],
                )),
                ("recovery_date", models.DateField(blank=True, null=True)),
                ("treatment", models.CharField(blank=True, max_length=120)),
                ("description", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("player", models.ForeignKey(
                    on_delete=models.deletion.CASCADE,
                    related_name="injury_records",
                    to="rotations.player",
                )),
            ],
            options={"ordering": ["-injury_date"]},
        ),
    ]
