from django.core.management.base import BaseCommand
from movies.tasks import translate_movie_titles


class Command(BaseCommand):
    help = "Translate titles of movies.AlternativeMovieTitle objects"

    def handle(self, *args, **options):
        translate_movie_titles(1000)
