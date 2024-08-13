from django.core.management.base import BaseCommand
from movies.tasks import wikidata_download


class Command(BaseCommand):
    help = "Imports movie data (id and sitelink count) from Wikidata"

    def handle(self, *args, **options):
        # top 5000 movies, 500 per request
        wikidata_download(5000, 500)
