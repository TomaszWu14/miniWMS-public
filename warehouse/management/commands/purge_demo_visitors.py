"""Usuwa wpisy odwiedzających demo starsze niż 90 dni (do crona / Scheduled Task)."""

from django.core.management.base import BaseCommand

from warehouse.models import DemoVisitor


class Command(BaseCommand):
    help = "Usuwa odwiedzających demo starszych niż 90 dni."

    def handle(self, *args, **options):
        self.stdout.write(f"Usunięto: {DemoVisitor.purge_old()}")
