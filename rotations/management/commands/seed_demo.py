from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from rotations.models import Club, InjuryAssessment, Player, RotationPlan, TrainingLoad


class Command(BaseCommand):
    help = "Create a larger demo dataset for injury risk analytics."

    def handle(self, *args, **options):
        RotationPlan.objects.all().delete()
        InjuryAssessment.objects.all().delete()
        TrainingLoad.objects.all().delete()
        Player.objects.all().delete()
        Club.objects.all().delete()

        clubs = {
            "ARS": Club.objects.create(
                name="Arsenal",
                short_name="ARS",
                city="London",
                stadium="Emirates Stadium",
                medical_budget=Decimal("28.50"),
            ),
            "MCI": Club.objects.create(
                name="Manchester City",
                short_name="MCI",
                city="Manchester",
                stadium="Etihad Stadium",
                medical_budget=Decimal("35.00"),
            ),
            "LIV": Club.objects.create(
                name="Liverpool",
                short_name="LIV",
                city="Liverpool",
                stadium="Anfield",
                medical_budget=Decimal("30.75"),
            ),
            "TOT": Club.objects.create(
                name="Tottenham Hotspur",
                short_name="TOT",
                city="London",
                stadium="Tottenham Hotspur Stadium",
                medical_budget=Decimal("27.20"),
            ),
            "CHE": Club.objects.create(
                name="Chelsea",
                short_name="CHE",
                city="London",
                stadium="Stamford Bridge",
                medical_budget=Decimal("32.40"),
            ),
            "NEW": Club.objects.create(
                name="Newcastle United",
                short_name="NEW",
                city="Newcastle upon Tyne",
                stadium="St James' Park",
                medical_budget=Decimal("24.80"),
            ),
            "AVL": Club.objects.create(
                name="Aston Villa",
                short_name="AVL",
                city="Birmingham",
                stadium="Villa Park",
                medical_budget=Decimal("22.60"),
            ),
            "BHA": Club.objects.create(
                name="Brighton & Hove Albion",
                short_name="BHA",
                city="Brighton",
                stadium="Amex Stadium",
                medical_budget=Decimal("18.90"),
            ),
            "MUN": Club.objects.create(
                name="Manchester United",
                short_name="MUN",
                city="Manchester",
                stadium="Old Trafford",
                medical_budget=Decimal("33.10"),
            ),
            "WHU": Club.objects.create(
                name="West Ham United",
                short_name="WHU",
                city="London",
                stadium="London Stadium",
                medical_budget=Decimal("19.70"),
            ),
            "BOU": Club.objects.create(
                name="AFC Bournemouth",
                short_name="BOU",
                city="Bournemouth",
                stadium="Vitality Stadium",
                medical_budget=Decimal("16.40"),
            ),
            "BRE": Club.objects.create(
                name="Brentford",
                short_name="BRE",
                city="London",
                stadium="Gtech Community Stadium",
                medical_budget=Decimal("15.80"),
            ),
            "CRY": Club.objects.create(
                name="Crystal Palace",
                short_name="CRY",
                city="London",
                stadium="Selhurst Park",
                medical_budget=Decimal("17.30"),
            ),
            "EVE": Club.objects.create(
                name="Everton",
                short_name="EVE",
                city="Liverpool",
                stadium="Goodison Park",
                medical_budget=Decimal("18.20"),
            ),
            "FUL": Club.objects.create(
                name="Fulham",
                short_name="FUL",
                city="London",
                stadium="Craven Cottage",
                medical_budget=Decimal("16.90"),
            ),
            "IPS": Club.objects.create(
                name="Ipswich Town",
                short_name="IPS",
                city="Ipswich",
                stadium="Portman Road",
                medical_budget=Decimal("12.80"),
            ),
            "LEI": Club.objects.create(
                name="Leicester City",
                short_name="LEI",
                city="Leicester",
                stadium="King Power Stadium",
                medical_budget=Decimal("17.60"),
            ),
            "NFO": Club.objects.create(
                name="Nottingham Forest",
                short_name="NFO",
                city="Nottingham",
                stadium="City Ground",
                medical_budget=Decimal("17.10"),
            ),
            "SOU": Club.objects.create(
                name="Southampton",
                short_name="SOU",
                city="Southampton",
                stadium="St Mary's Stadium",
                medical_budget=Decimal("14.70"),
            ),
            "WOL": Club.objects.create(
                name="Wolverhampton Wanderers",
                short_name="WOL",
                city="Wolverhampton",
                stadium="Molineux Stadium",
                medical_budget=Decimal("15.90"),
            ),
        }

        player_rows = [
            ("ARS", "Bukayo Saka", Player.Position.FORWARD, 24, "England", "Left", "120.00", 428, 58),
            ("ARS", "Declan Rice", Player.Position.MIDFIELDER, 27, "England", "Right", "95.00", 450, 25),
            ("ARS", "Martin Odegaard", Player.Position.MIDFIELDER, 27, "Norway", "Left", "92.00", 405, 36),
            ("ARS", "William Saliba", Player.Position.DEFENDER, 25, "France", "Right", "82.00", 440, 32),
            ("ARS", "Gabriel Martinelli", Player.Position.FORWARD, 25, "Brazil", "Right", "68.00", 352, 46),
            ("MCI", "Erling Haaland", Player.Position.FORWARD, 25, "Norway", "Left", "160.00", 385, 48),
            ("MCI", "Phil Foden", Player.Position.MIDFIELDER, 25, "England", "Left", "105.00", 365, 30),
            ("MCI", "Rodri", Player.Position.MIDFIELDER, 29, "Spain", "Right", "115.00", 310, 78),
            ("MCI", "Kevin De Bruyne", Player.Position.MIDFIELDER, 34, "Belgium", "Right", "38.00", 290, 76),
            ("MCI", "Ruben Dias", Player.Position.DEFENDER, 28, "Portugal", "Right", "70.00", 410, 40),
            ("LIV", "Mohamed Salah", Player.Position.FORWARD, 33, "Egypt", "Left", "58.00", 420, 45),
            ("LIV", "Virgil van Dijk", Player.Position.DEFENDER, 34, "Netherlands", "Right", "32.00", 430, 72),
            ("LIV", "Alexis Mac Allister", Player.Position.MIDFIELDER, 27, "Argentina", "Right", "70.00", 398, 35),
            ("LIV", "Trent Alexander-Arnold", Player.Position.DEFENDER, 27, "England", "Right", "75.00", 370, 54),
            ("LIV", "Luis Diaz", Player.Position.FORWARD, 29, "Colombia", "Right", "62.00", 358, 43),
            ("TOT", "Son Heung-min", Player.Position.FORWARD, 33, "South Korea", "Right", "40.00", 360, 44),
            ("TOT", "James Maddison", Player.Position.MIDFIELDER, 29, "England", "Right", "50.00", 335, 65),
            ("TOT", "Micky van de Ven", Player.Position.DEFENDER, 25, "Netherlands", "Left", "60.00", 275, 88),
            ("TOT", "Cristian Romero", Player.Position.DEFENDER, 27, "Argentina", "Right", "55.00", 390, 56),
            ("TOT", "Dejan Kulusevski", Player.Position.FORWARD, 26, "Sweden", "Left", "55.00", 346, 38),
            ("CHE", "Cole Palmer", Player.Position.MIDFIELDER, 24, "England", "Left", "110.00", 445, 42),
            ("CHE", "Enzo Fernandez", Player.Position.MIDFIELDER, 25, "Argentina", "Right", "70.00", 412, 39),
            ("CHE", "Reece James", Player.Position.DEFENDER, 26, "England", "Right", "38.00", 210, 86),
            ("CHE", "Moises Caicedo", Player.Position.MIDFIELDER, 24, "Ecuador", "Right", "85.00", 430, 31),
            ("CHE", "Levi Colwill", Player.Position.DEFENDER, 23, "England", "Left", "50.00", 325, 47),
            ("NEW", "Alexander Isak", Player.Position.FORWARD, 26, "Sweden", "Right", "90.00", 360, 62),
            ("NEW", "Bruno Guimaraes", Player.Position.MIDFIELDER, 28, "Brazil", "Right", "80.00", 442, 35),
            ("NEW", "Anthony Gordon", Player.Position.FORWARD, 25, "England", "Right", "65.00", 410, 41),
            ("NEW", "Sven Botman", Player.Position.DEFENDER, 26, "Netherlands", "Left", "45.00", 250, 79),
            ("NEW", "Kieran Trippier", Player.Position.DEFENDER, 35, "England", "Right", "8.00", 300, 68),
            ("AVL", "Ollie Watkins", Player.Position.FORWARD, 30, "England", "Right", "62.00", 430, 34),
            ("AVL", "Emiliano Martinez", Player.Position.GOALKEEPER, 33, "Argentina", "Right", "28.00", 450, 22),
            ("AVL", "John McGinn", Player.Position.MIDFIELDER, 31, "Scotland", "Left", "22.00", 395, 51),
            ("AVL", "Youri Tielemans", Player.Position.MIDFIELDER, 29, "Belgium", "Right", "30.00", 340, 48),
            ("AVL", "Pau Torres", Player.Position.DEFENDER, 29, "Spain", "Left", "36.00", 365, 44),
            ("BHA", "Kaoru Mitoma", Player.Position.FORWARD, 29, "Japan", "Right", "45.00", 315, 66),
            ("BHA", "Joao Pedro", Player.Position.FORWARD, 24, "Brazil", "Right", "55.00", 390, 37),
            ("BHA", "Lewis Dunk", Player.Position.DEFENDER, 34, "England", "Right", "10.00", 420, 59),
            ("BHA", "Pervis Estupinan", Player.Position.DEFENDER, 28, "Ecuador", "Left", "30.00", 285, 73),
            ("BHA", "Evan Ferguson", Player.Position.FORWARD, 21, "Ireland", "Right", "40.00", 240, 52),
            ("MUN", "Bruno Fernandes", Player.Position.MIDFIELDER, 31, "Portugal", "Right", "58.00", 448, 33),
            ("MUN", "Marcus Rashford", Player.Position.FORWARD, 28, "England", "Right", "55.00", 330, 60),
            ("MUN", "Kobbie Mainoo", Player.Position.MIDFIELDER, 21, "England", "Right", "65.00", 335, 29),
            ("MUN", "Lisandro Martinez", Player.Position.DEFENDER, 28, "Argentina", "Left", "45.00", 260, 83),
            ("MUN", "Rasmus Hojlund", Player.Position.FORWARD, 23, "Denmark", "Left", "62.00", 345, 55),
            ("WHU", "Jarrod Bowen", Player.Position.FORWARD, 29, "England", "Left", "50.00", 418, 40),
            ("WHU", "Mohammed Kudus", Player.Position.MIDFIELDER, 25, "Ghana", "Left", "48.00", 376, 49),
            ("WHU", "Lucas Paqueta", Player.Position.MIDFIELDER, 28, "Brazil", "Left", "45.00", 388, 46),
            ("WHU", "Edson Alvarez", Player.Position.MIDFIELDER, 28, "Mexico", "Right", "32.00", 356, 57),
            ("WHU", "Alphonse Areola", Player.Position.GOALKEEPER, 33, "France", "Right", "9.00", 450, 28),
            ("BOU", "Dominic Solanke", Player.Position.FORWARD, 28, "England", "Right", "40.00", 430, 35),
            ("BOU", "Antoine Semenyo", Player.Position.FORWARD, 26, "Ghana", "Right", "32.00", 365, 43),
            ("BOU", "Ryan Christie", Player.Position.MIDFIELDER, 31, "Scotland", "Left", "12.00", 380, 48),
            ("BOU", "Illia Zabarnyi", Player.Position.DEFENDER, 23, "Ukraine", "Right", "35.00", 440, 30),
            ("BOU", "Neto", Player.Position.GOALKEEPER, 36, "Brazil", "Right", "5.00", 360, 58),
            ("BRE", "Ivan Toney", Player.Position.FORWARD, 30, "England", "Right", "35.00", 310, 52),
            ("BRE", "Bryan Mbeumo", Player.Position.FORWARD, 26, "Cameroon", "Left", "45.00", 390, 61),
            ("BRE", "Yoane Wissa", Player.Position.FORWARD, 29, "DR Congo", "Right", "28.00", 335, 44),
            ("BRE", "Christian Norgaard", Player.Position.MIDFIELDER, 32, "Denmark", "Right", "14.00", 405, 55),
            ("BRE", "Ethan Pinnock", Player.Position.DEFENDER, 33, "Jamaica", "Left", "10.00", 420, 50),
            ("CRY", "Eberechi Eze", Player.Position.MIDFIELDER, 27, "England", "Right", "60.00", 340, 67),
            ("CRY", "Michael Olise", Player.Position.MIDFIELDER, 24, "France", "Left", "65.00", 285, 74),
            ("CRY", "Marc Guehi", Player.Position.DEFENDER, 25, "England", "Right", "45.00", 395, 38),
            ("CRY", "Jean-Philippe Mateta", Player.Position.FORWARD, 29, "France", "Right", "28.00", 360, 41),
            ("CRY", "Joachim Andersen", Player.Position.DEFENDER, 30, "Denmark", "Right", "25.00", 430, 45),
            ("EVE", "Jordan Pickford", Player.Position.GOALKEEPER, 32, "England", "Left", "22.00", 450, 24),
            ("EVE", "Jarrad Branthwaite", Player.Position.DEFENDER, 23, "England", "Left", "42.00", 415, 32),
            ("EVE", "James Tarkowski", Player.Position.DEFENDER, 33, "England", "Right", "8.00", 440, 46),
            ("EVE", "Dominic Calvert-Lewin", Player.Position.FORWARD, 29, "England", "Right", "18.00", 280, 82),
            ("EVE", "Abdoulaye Doucoure", Player.Position.MIDFIELDER, 33, "Mali", "Right", "10.00", 340, 54),
            ("FUL", "Bernd Leno", Player.Position.GOALKEEPER, 34, "Germany", "Right", "10.00", 450, 26),
            ("FUL", "Joao Palhinha", Player.Position.MIDFIELDER, 30, "Portugal", "Right", "45.00", 410, 39),
            ("FUL", "Andreas Pereira", Player.Position.MIDFIELDER, 30, "Brazil", "Right", "22.00", 370, 42),
            ("FUL", "Antonee Robinson", Player.Position.DEFENDER, 28, "United States", "Left", "25.00", 430, 34),
            ("FUL", "Rodrigo Muniz", Player.Position.FORWARD, 25, "Brazil", "Right", "20.00", 310, 47),
            ("IPS", "Leif Davis", Player.Position.DEFENDER, 26, "England", "Left", "20.00", 430, 36),
            ("IPS", "Conor Chaplin", Player.Position.MIDFIELDER, 29, "England", "Left", "8.00", 350, 44),
            ("IPS", "Sam Morsy", Player.Position.MIDFIELDER, 34, "Egypt", "Right", "4.00", 410, 52),
            ("IPS", "Omari Hutchinson", Player.Position.FORWARD, 22, "England", "Left", "28.00", 330, 31),
            ("IPS", "George Hirst", Player.Position.FORWARD, 27, "England", "Right", "8.00", 260, 64),
            ("LEI", "Jamie Vardy", Player.Position.FORWARD, 39, "England", "Right", "2.00", 270, 76),
            ("LEI", "Kiernan Dewsbury-Hall", Player.Position.MIDFIELDER, 27, "England", "Left", "35.00", 420, 37),
            ("LEI", "Wilfred Ndidi", Player.Position.MIDFIELDER, 29, "Nigeria", "Right", "18.00", 350, 59),
            ("LEI", "Wout Faes", Player.Position.DEFENDER, 28, "Belgium", "Right", "18.00", 430, 43),
            ("LEI", "Mads Hermansen", Player.Position.GOALKEEPER, 25, "Denmark", "Right", "14.00", 450, 21),
            ("NFO", "Morgan Gibbs-White", Player.Position.MIDFIELDER, 26, "England", "Right", "45.00", 420, 33),
            ("NFO", "Taiwo Awoniyi", Player.Position.FORWARD, 28, "Nigeria", "Right", "28.00", 250, 84),
            ("NFO", "Anthony Elanga", Player.Position.FORWARD, 24, "Sweden", "Right", "30.00", 365, 45),
            ("NFO", "Murillo", Player.Position.DEFENDER, 24, "Brazil", "Left", "45.00", 430, 29),
            ("NFO", "Danilo", Player.Position.MIDFIELDER, 25, "Brazil", "Right", "28.00", 320, 68),
            ("SOU", "Kyle Walker-Peters", Player.Position.DEFENDER, 29, "England", "Right", "18.00", 420, 41),
            ("SOU", "Adam Armstrong", Player.Position.FORWARD, 29, "England", "Right", "14.00", 390, 47),
            ("SOU", "James Ward-Prowse", Player.Position.MIDFIELDER, 31, "England", "Right", "20.00", 405, 36),
            ("SOU", "Jan Bednarek", Player.Position.DEFENDER, 30, "Poland", "Right", "12.00", 430, 44),
            ("SOU", "Che Adams", Player.Position.FORWARD, 30, "Scotland", "Right", "12.00", 310, 56),
            ("WOL", "Pedro Neto", Player.Position.FORWARD, 26, "Portugal", "Left", "42.00", 260, 86),
            ("WOL", "Matheus Cunha", Player.Position.FORWARD, 27, "Brazil", "Right", "45.00", 380, 48),
            ("WOL", "Rayan Ait-Nouri", Player.Position.DEFENDER, 25, "Algeria", "Left", "35.00", 360, 50),
            ("WOL", "Mario Lemina", Player.Position.MIDFIELDER, 32, "Gabon", "Right", "10.00", 390, 58),
            ("WOL", "Max Kilman", Player.Position.DEFENDER, 28, "England", "Left", "35.00", 440, 33),
        ]

        today = timezone.localdate()
        players = []
        for index, row in enumerate(player_rows):
            club_code, full_name, position, age, nationality, foot, value, minutes, history = row
            career_injuries = max(0, min(20, round(history / 10)))
            season_injuries = max(0, min(8, round(history / 28)))
            season_minutes = max(120, min(3600, minutes * 6 + (index * 37) % 600))
            last_injury_date = today - timedelta(days=14 + index * 9)
            player = Player.objects.create(
                club=clubs[club_code],
                full_name=full_name,
                position=position,
                age=age,
                nationality=nationality,
                dominant_foot=foot,
                market_value=Decimal(value),
                season_minutes=season_minutes,
                last_injury_date=last_injury_date,
                season_injuries=season_injuries,
                career_injuries=career_injuries,
                minutes_last_5=minutes,
                previous_injuries=career_injuries,
                injury_history_score=career_injuries * 10,
                is_available=season_injuries < 3,
            )
            players.append(player)

            for load_index, days_ago in enumerate([24, 18, 12, 6, 2]):
                TrainingLoad.objects.create(
                    player=player,
                    date=today - timedelta(days=days_ago),
                    minutes_played=max(20, min(110, minutes // 5 + load_index * 4 - index % 5)),
                    distance_km=Decimal(str(round(6.5 + (minutes / 100) + load_index * 0.25, 2))),
                    sprint_count=max(8, min(62, 18 + index * 2 + load_index * 3)),
                    accelerations=max(25, min(105, 42 + index * 3 + load_index * 4)),
                    perceived_exertion=max(4, min(10, 5 + index % 4 + load_index // 2)),
                    sleep_hours=Decimal(str(round(8.2 - (history / 100) - load_index * 0.12, 1))),
                    soreness_level=max(1, min(10, 2 + history // 18 + load_index // 2)),
                )

            for assessment_index, days_ago in enumerate([20, 10, 1]):
                fatigue = max(20, min(98, 35 + history // 2 + assessment_index * 10 + index % 7))
                InjuryAssessment.objects.create(
                    player=player,
                    date=today - timedelta(days=days_ago),
                    muscle_fatigue=fatigue,
                    joint_stability=max(25, min(94, 88 - history // 2 - assessment_index * 7)),
                    previous_injury_factor=career_injuries,
                    recovery_score=max(25, min(95, 86 - history // 2 - assessment_index * 6)),
                    notes="Risk is calculated from season minutes, last injury date, season injuries and career injuries.",
                )

        opponents = ["Chelsea", "Newcastle United", "Aston Villa", "Brighton"]
        for index, player in enumerate(players):
            latest_assessment = player.latest_assessment
            score = float(latest_assessment.risk_score)
            if score >= 65:
                recommendation = RotationPlan.Recommendation.MEDICAL_REVIEW
                minutes = 0
            elif score >= 55:
                recommendation = RotationPlan.Recommendation.REST
                minutes = 0
            elif score >= 38:
                recommendation = RotationPlan.Recommendation.LIMITED
                minutes = 45
            else:
                recommendation = RotationPlan.Recommendation.START
                minutes = 75
            RotationPlan.objects.create(
                player=player,
                assessment=latest_assessment,
                match_date=today + timedelta(days=3 + index % 4),
                opponent=opponents[index % len(opponents)],
                planned_minutes=minutes,
                recommendation=recommendation,
                rationale=f"Latest risk is {score:.1f}%; season minutes: {player.season_minutes}.",
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Demo data created: {len(clubs)} clubs, {len(players)} players, "
                "training loads, risk assessments and hidden rotation plans."
            )
        )
