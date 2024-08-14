from django.core.management.base import BaseCommand
from movies.tasks.translation import MovieTitleTranslator, LANGUAGE_MAP
from movies.models import AlternativeMovieTitle


class Command(BaseCommand):
    help = "Translate titles of movies.AlternativeMovieTitle objects"

    def handle(self, *args, **options):
        untranslated = AlternativeMovieTitle.objects.filter(
            translated_title="", language_code__in=LANGUAGE_MAP.keys()
        ).exclude(movie__english_title="")

        MovieTitleTranslator(untranslated).run()
