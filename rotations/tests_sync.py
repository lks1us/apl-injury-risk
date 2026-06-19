from unittest.mock import patch

from django.test import TestCase

from rotations.models import Club, DataSyncLog, Player
from rotations.services.fpl_sync import sync_fpl_data


SAMPLE_FPL_PAYLOAD = {
    "teams": [
        {
            "id": 1,
            "name": "Arsenal",
            "short_name": "ARS",
            "strength": 5,
        },
        {
            "id": 2,
            "name": "Chelsea",
            "short_name": "CHE",
            "strength": 4,
        },
    ],
    "elements": [
        {
            "id": 101,
            "team": 1,
            "element_type": 3,
            "first_name": "Test",
            "second_name": "Midfielder",
            "web_name": "Midfielder",
            "birth_date": "1998-03-12",
            "minutes": 2100,
            "now_cost": 75,
            "status": "a",
            "news": "",
            "news_added": None,
            "chance_of_playing_this_round": 100,
            "removed": False,
        },
        {
            "id": 102,
            "team": 2,
            "element_type": 2,
            "first_name": "Injured",
            "second_name": "Defender",
            "web_name": "Defender",
            "birth_date": "1995-07-01",
            "minutes": 900,
            "now_cost": 45,
            "status": "i",
            "news": "Knee injury - Expected back 01 Apr",
            "news_added": "2026-03-01T12:00:00Z",
            "chance_of_playing_this_round": 0,
            "removed": False,
        },
    ],
}


class FPLSyncTests(TestCase):
    @patch("rotations.services.fpl_sync.fetch_fpl_payload")
    def test_sync_fpl_data_imports_players_and_clubs(self, fetch_mock):
        fetch_mock.return_value = SAMPLE_FPL_PAYLOAD

        log = sync_fpl_data(force=True)

        self.assertEqual(log.status, DataSyncLog.Status.SUCCESS)
        self.assertEqual(log.players_synced, 2)
        self.assertEqual(log.clubs_synced, 2)
        self.assertEqual(Player.objects.filter(data_source=Player.DataSource.FPL).count(), 2)
        self.assertTrue(Club.objects.filter(short_name="ARS").exists())

        injured = Player.objects.get(external_id=102)
        self.assertFalse(injured.is_available)
        self.assertIsNotNone(injured.latest_assessment)
