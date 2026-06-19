from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("rotations", "0003_player_season_risk_fields"),
    ]

    operations = [
        migrations.AddField(
            model_name="injuryassessment",
            name="career_injuries_at_assessment",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Player career injuries at the time of this assessment.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="injuryassessment",
            name="last_injury_date_at_assessment",
            field=models.DateField(
                blank=True,
                help_text="Player last injury date at the time of this assessment.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="injuryassessment",
            name="season_injuries_at_assessment",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Player season injuries at the time of this assessment.",
                null=True,
            ),
        ),
        migrations.AddField(
            model_name="injuryassessment",
            name="season_minutes_at_assessment",
            field=models.PositiveSmallIntegerField(
                blank=True,
                help_text="Player season minutes at the time of this assessment.",
                null=True,
            ),
        ),
    ]
