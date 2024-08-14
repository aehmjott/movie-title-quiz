from django.core.management.base import BaseCommand
from movies.tasks.wikidata import WikidataAPI
from movies.models import Movie


class Command(BaseCommand):
    help = "Imports details from Wikidata for existing ``movies.Movie`` objects"

    def handle(self, *args, **options):
        incomplete_movies = Movie.objects.filter(english_title="")[:10]
        WikidataAPI(incomplete_movies).run()
