from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .analytics import assessment_trend, player_risk_projection, training_load_chart
from .forms import InjuryUpdateForm, PlayerForm, RotationPlanForm, TrainingLoadForm
from .models import Club, InjuryAssessment, InjuryRecord, Player, RotationPlan, TrainingLoad


class RotationRiskTests(TestCase):
    def setUp(self):
        self.club = Club.objects.create(
            name="Test United",
            short_name="TST",
            city="London",
            stadium="Test Arena",
            medical_budget=Decimal("12.50"),
        )
        self.player = Player.objects.create(
            club=self.club,
            full_name="Alex Tester",
            position=Player.Position.MIDFIELDER,
            age=24,
            nationality="England",
            dominant_foot="Right",
            market_value=Decimal("20.00"),
            season_minutes=3200,
            season_injuries=2,
            career_injuries=10,
            last_injury_date=timezone.localdate() - timedelta(days=20),
            minutes_last_5=420,
            previous_injuries=8,
            injury_history_score=55,
        )

    def test_assessment_calculates_score_and_level(self):
        assessment = InjuryAssessment.objects.create(
            player=self.player,
            date=timezone.localdate(),
            muscle_fatigue=90,
            joint_stability=40,
            previous_injury_factor=70,
            recovery_score=35,
            notes="High fatigue",
        )

        self.assertGreaterEqual(assessment.risk_score, 65)
        self.assertEqual(assessment.risk_level, InjuryAssessment.RiskLevel.HIGH)

    def test_player_form_rejects_impossible_minutes(self):
        form = PlayerForm(
            data={
                "club": self.club.pk,
                "full_name": "Load Monster",
                "position": Player.Position.FORWARD,
                "season_minutes": 4500,
                "season_injuries": 0,
                "career_injuries": 0,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("season_minutes", form.errors)

    def test_player_form_creates_injury_with_zone_and_severity(self):
        form = PlayerForm(
            data={
                "club": self.club.pk,
                "full_name": "New Player",
                "position": Player.Position.FORWARD,
                "season_minutes": 1200,
                "injury_severity": InjuryRecord.Severity.MODERATE,
                "injury_body_part": InjuryRecord.BodyPart.HAMSTRING,
            }
        )
        self.assertTrue(form.is_valid())
        player = form.save()
        injury = form.create_injury_record(player)
        self.assertIsNotNone(injury)
        self.assertEqual(injury.severity, InjuryRecord.Severity.MODERATE)
        self.assertEqual(injury.body_part, InjuryRecord.BodyPart.HAMSTRING)

    def test_player_form_requires_both_injury_fields(self):
        form = PlayerForm(
            data={
                "club": self.club.pk,
                "full_name": "Partial Injury",
                "position": Player.Position.FORWARD,
                "season_minutes": 900,
                "injury_severity": InjuryRecord.Severity.MINOR,
            }
        )
        self.assertFalse(form.is_valid())
        self.assertIn("injury_body_part", form.errors)

    def test_training_load_form_rejects_future_date(self):
        form = TrainingLoadForm(
            data={
                "date": timezone.localdate() + timedelta(days=1),
                "minutes_played": 90,
                "distance_km": "10.2",
                "sprint_count": 24,
                "accelerations": 64,
                "perceived_exertion": 8,
                "sleep_hours": "7.3",
                "soreness_level": 5,
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("date", form.errors)

    def test_rotation_plan_form_rejects_rest_with_minutes(self):
        form = RotationPlanForm(
            player=self.player,
            data={
                "assessment": "",
                "match_date": timezone.localdate() + timedelta(days=3),
                "opponent": "Demo FC",
                "planned_minutes": 25,
                "recommendation": RotationPlan.Recommendation.REST,
                "rationale": "Needs recovery.",
            },
        )

        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors)

    def test_injury_update_form_saves_record(self):
        form = InjuryUpdateForm(
            data={
                "injury_date": (timezone.localdate() - timedelta(days=5)).isoformat(),
                "body_part": InjuryRecord.BodyPart.KNEE,
                "severity": InjuryRecord.Severity.SEVERE,
            }
        )
        self.assertTrue(form.is_valid())
        injury = form.save_for_player(self.player)
        self.player.refresh_from_db()
        self.assertEqual(injury.body_part, InjuryRecord.BodyPart.KNEE)
        self.assertEqual(self.player.last_injury_date, injury.injury_date)

    def test_analytics_returns_projection_and_chart_data(self):
        TrainingLoad.objects.create(
            player=self.player,
            date=timezone.localdate() - timedelta(days=2),
            minutes_played=95,
            distance_km=Decimal("11.40"),
            sprint_count=35,
            accelerations=76,
            perceived_exertion=8,
            sleep_hours=Decimal("6.8"),
            soreness_level=6,
        )
        InjuryAssessment.objects.create(
            player=self.player,
            date=timezone.localdate() - timedelta(days=1),
            muscle_fatigue=74,
            joint_stability=58,
            previous_injury_factor=55,
            recovery_score=52,
            notes="Moderate risk",
        )

        projection = player_risk_projection(self.player)
        trend = assessment_trend(self.player)
        load_chart = training_load_chart(self.player)

        self.assertIn("projected_score", projection)
        self.assertEqual(len(trend["labels"]), 1)
        self.assertEqual(len(load_chart["loads"]), 1)
