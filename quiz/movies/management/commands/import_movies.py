from django.core.management.base import BaseCommand, CommandError
from movies.tasks import import_movies

class Command(BaseCommand):
    help = "Imports movie data from a json file"

    def handle(self, *args, **options):
        import_movies()