from django.core.management.base import BaseCommand
from movies.tasks.wikidata import WikidataGraphAPI


class Command(BaseCommand):
    help = "Imports movie data (id and sitelink count) from Wikidata"

    def add_arguments(self, parser):
        parser.add_argument("count", type=int)

    def handle(self, *args, **options):
        WikidataGraphAPI().run(options["count"])
