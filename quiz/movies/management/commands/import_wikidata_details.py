from django.core.management.base import BaseCommand
from movies.tasks import wikidata_detail_download


class Command(BaseCommand):
    help = "Imports movie data from Wikidata for existing ``movies.Movie`´` objects"

    def handle(self, *args, **options):
        wikidata_detail_download()
