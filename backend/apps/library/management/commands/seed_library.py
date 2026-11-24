"""
Charge le cahier de douâas et hadiths dans la base (idempotent).

Usage :
    python manage.py seed_library            # crée ou met à jour par source
    python manage.py seed_library --reset    # vide les tables puis recharge
"""
from django.core.management.base import BaseCommand

from apps.library.content import DUAS, HADITHS
from apps.library.models import Dua, Hadith


class Command(BaseCommand):
    help = "Charge le cahier de douâas et hadiths du Prophète ﷺ (idempotent)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reset",
            action="store_true",
            help="Vide les tables douâas/hadiths avant le chargement.",
        )

    def handle(self, *args, **options):
        if options["reset"]:
            deleted_duas, _ = Dua.objects.all().delete()
            deleted_hadiths, _ = Hadith.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    f"Tables vidées : {deleted_duas} douâas, {deleted_hadiths} hadiths."
                )
            )

        duas_created = duas_updated = 0
        for item in DUAS:
            _, created = Dua.objects.update_or_create(
                source=item["source"],
                title=item["title"],
                defaults={k: v for k, v in item.items() if k not in ("source", "title")},
            )
            duas_created += created
            duas_updated += not created

        hadiths_created = hadiths_updated = 0
        for item in HADITHS:
            _, created = Hadith.objects.update_or_create(
                source=item["source"],
                title=item["title"],
                defaults={k: v for k, v in item.items() if k not in ("source", "title")},
            )
            hadiths_created += created
            hadiths_updated += not created

        self.stdout.write(
            self.style.SUCCESS(
                f"Douâas : {duas_created} créés, {duas_updated} mis à jour. "
                f"Hadiths : {hadiths_created} créés, {hadiths_updated} mis à jour."
            )
        )
