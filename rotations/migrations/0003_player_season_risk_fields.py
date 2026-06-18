# Generated for simplified season injury risk factors.
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rotations", "0002_player_previous_injuries"),
    ]

    operations = [
        migrations.AddField(
            model_name="player",
            name="career_injuries",
            field=models.PositiveSmallIntegerField(
                default=0,
                validators=[MinValueValidator(0), MaxValueValidator(60)],
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="last_injury_date",
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="player",
            name="season_injuries",
            field=models.PositiveSmallIntegerField(
                default=0,
                validators=[MinValueValidator(0), MaxValueValidator(20)],
            ),
        ),
        migrations.AddField(
            model_name="player",
            name="season_minutes",
            field=models.PositiveSmallIntegerField(
                default=0,
                help_text="Minutes played during the current season.",
                validators=[MinValueValidator(0), MaxValueValidator(4000)],
            ),
        ),
    ]
