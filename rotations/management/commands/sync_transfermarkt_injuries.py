from django.core.management.base import BaseCommand

from rotations.services.transfermarkt_sync import sync_transfermarkt_injuries


class Command(BaseCommand):
    help = "Load latest player injuries from Transfermarkt."

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="Refresh injuries for all FPL players.")
        parser.add_argument("--club", type=str, help="Club short code, e.g. ARS.")
        parser.add_argument("--limit", type=int, default=9999, help="Maximum players to sync.")

    def handle(self, *args, **options):
        log = sync_transfermarkt_injuries(
            force=options["force"],
            batch_size=options["limit"],
            club_short_name=options.get("club"),
        )
        if log.status == log.Status.SUCCESS:
            self.stdout.write(self.style.SUCCESS(log.message))
        else:
            self.stdout.write(self.style.WARNING(log.message))
