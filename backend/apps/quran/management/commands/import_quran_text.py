"""
Importe le texte du Coran (arabe Uthmani + traductions) dans la base locale.

Source : Quran.com API v4 (via `quran_client`), appelée UNE fois par sourate.
L'import est idempotent : le relancer met à jour sans dupliquer.

Usage :
    python manage.py import_quran_text                      # fr + en, 114 sourates
    python manage.py import_quran_text --translations fr    # une seule langue
    python manage.py import_quran_text --surah 1 --surah 2  # quelques sourates
    python manage.py import_quran_text --reset              # vide puis réimporte
"""
import time

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.quran.models import Surah, Verse, VerseTranslation
from apps.quran.services import local_text, quran_client

# Langues importables : celles dont l'ID de ressource est connu.
IMPORTABLE = ("fr", "en")


class Command(BaseCommand):
    help = "Importe le texte du Coran et ses traductions (fr, en) dans la base."

    def add_arguments(self, parser):
        parser.add_argument(
            "--translations", default="fr,en",
            help="Langues à importer, séparées par des virgules (défaut : fr,en).",
        )
        parser.add_argument(
            "--surah", type=int, action="append", dest="surahs",
            help="Limiter à une sourate (option répétable). Défaut : les 114.",
        )
        parser.add_argument("--reset", action="store_true", help="Vide les tables avant l'import.")
        parser.add_argument(
            "--pause", type=float, default=0.3,
            help="Pause en secondes entre deux sourates (politesse envers l'API).",
        )

    def handle(self, *args, **options):
        codes = [c.strip() for c in options["translations"].split(",") if c.strip()]
        unknown = [c for c in codes if c not in IMPORTABLE]
        if unknown:
            raise CommandError(f"Langue(s) non prises en charge : {', '.join(unknown)} (choix : {', '.join(IMPORTABLE)}).")
        wanted = options["surahs"] or list(range(1, 115))
        if any(not 1 <= n <= 114 for n in wanted):
            raise CommandError("Les numéros de sourate doivent être compris entre 1 et 114.")

        if options["reset"]:
            VerseTranslation.objects.all().delete()
            Verse.objects.all().delete()
            Surah.objects.all().delete()
            self.stdout.write(self.style.WARNING("Tables Coran vidées."))

        try:
            chapters = {c["number"]: c for c in quran_client.fetch_surahs()}
        except quran_client.QuranAPIError as exc:
            raise CommandError(f"Liste des sourates indisponible : {exc}") from exc

        for index, number in enumerate(wanted):
            if index:
                time.sleep(options["pause"])
            try:
                verses = quran_client.fetch_verses(number, codes)
            except quran_client.QuranAPIError as exc:
                raise CommandError(f"Sourate {number} : {exc}") from exc
            chapter = chapters[number]
            if len(verses) != chapter["verses_count"]:
                raise CommandError(
                    f"Sourate {number} : {len(verses)} versets reçus, {chapter['verses_count']} attendus. "
                    "Import interrompu (rien n'est écrit pour cette sourate)."
                )
            self._store(chapter, verses, codes)
            self.stdout.write(f"  sourate {number:>3} : {len(verses)} versets")

        self.stdout.write(self.style.SUCCESS(f"Import terminé. Base : {local_text.stats()}"))

    @transaction.atomic
    def _store(self, chapter: dict, verses: list[dict], codes: list[str]) -> None:
        surah, _ = Surah.objects.update_or_create(
            number=chapter["number"],
            defaults={
                "name_arabic": chapter["name_arabic"],
                "name_transliterated": chapter["name_transliterated"],
                "verses_count": chapter["verses_count"],
                "revelation_place": chapter["revelation_place"],
            },
        )
        for item in verses:
            verse, _ = Verse.objects.update_or_create(
                surah=surah, ayah_number=item["ayah_number"],
                defaults={"text_uthmani": item["text_uthmani"]},
            )
            for tr in item["translations"]:
                if tr["code"] not in codes:
                    continue
                VerseTranslation.objects.update_or_create(
                    verse=verse, code=tr["code"],
                    defaults={"text": tr["text"], "resource_id": tr["resource_id"]},
                )
