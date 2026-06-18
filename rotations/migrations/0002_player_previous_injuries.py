# Generated for simplified injury risk scoring.
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rotations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="previous_injuries",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Number of previous injuries recorded for this player.",
                validators=[MinValueValidator(0), MaxValueValidator(20)],
            ),
        ),
        migrations.AlterField(
            model_name="player",
            name="injury_history_score",
            field=models.PositiveSmallIntegerField(
                default=20,
                help_text="Legacy historical factor from 0 to 100.",
                validators=[MinValueValidator(0), MaxValueValidator(100)],
            ),
        ),
    ]
