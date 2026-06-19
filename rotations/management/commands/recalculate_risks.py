from django.core.management.base import BaseCommand

from rotations.models import InjuryAssessment


class Command(BaseCommand):
    help = "Recalculate risk scores for all injury assessments."

    def handle(self, *args, **options):
        updated = 0
        for assessment in InjuryAssessment.objects.select_related("player").iterator():
            assessment.risk_score = assessment.calculate_risk_score()
            assessment.risk_level = InjuryAssessment.level_for_score(assessment.risk_score)
            assessment.save(update_fields=["risk_score", "risk_level"])
            updated += 1
        self.stdout.write(self.style.SUCCESS(f"Recalculated {updated} assessments."))
