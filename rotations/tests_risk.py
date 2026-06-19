from datetime import timedelta
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone

from .models import Club, InjuryAssessment, InjuryRecord, Player
from .risk_engine import calculate_player_risk


class RiskEngineTests(TestCase):
    def setUp(self):
        self.club = Club.objects.create(
            name="Risk FC",
            short_name="RFC",
            city="London",
            stadium="Test Arena",
            medical_budget=Decimal("12.50"),
        )
        self.player = Player.objects.create(
            club=self.club,
            full_name="Risk Tester",
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

    def test_high_risk_player_scores_above_threshold(self):
        result = calculate_player_risk(self.player)
        self.assertGreaterEqual(result["total"], 65)
        self.assertEqual(result["level"], InjuryAssessment.RiskLevel.HIGH)

    def test_healthy_goalkeeper_scores_lower(self):
        keeper = Player.objects.create(
            club=self.club,
            full_name="Safe Keeper",
            position=Player.Position.GOALKEEPER,
            age=26,
            nationality="England",
            dominant_foot="Right",
            market_value=Decimal("5.00"),
            season_minutes=900,
            season_injuries=0,
            career_injuries=1,
            minutes_last_5=180,
        )
        result = calculate_player_risk(keeper)
        self.assertLess(result["total"], 35)
