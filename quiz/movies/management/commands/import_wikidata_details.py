from django.core.management.base import BaseCommand
from movies.tasks.wikidata import WikidataAPI
from movies.models import Movie


class Command(BaseCommand):
    help = "Imports details from Wikidata for existing ``movies.Movie`` objects"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int)

    def handle(self, *args, **options):
        incomplete_movies = Movie.objects.filter(english_title="")[: options["count"]]
        WikidataAPI(incomplete_movies).run()
