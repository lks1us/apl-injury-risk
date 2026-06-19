from django.core.management.base import BaseCommand

from rotations.services.fpl_sync import sync_fpl_data


class Command(BaseCommand):
    help = "Download and update Premier League players from the public FPL API."

    def add_arguments(self, parser):
        parser.add_argument(
            "--force",
            action="store_true",
            help="Run sync even if the last successful sync is recent.",
        )

    def handle(self, *args, **options):
        log = sync_fpl_data(force=options["force"])
        if log.status == log.Status.SUCCESS:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Synced {log.players_synced} players from {log.clubs_synced} clubs."
                )
            )
        else:
            self.stdout.write(self.style.ERROR(f"Sync failed: {log.message}"))
