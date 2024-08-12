from datetime import timedelta, datetime, date

from django.conf import settings

from .models import Actor, Movie, AlternativeMovieTitle

import json


def parse_release_date(release_date: str) -> date:
    try:
        return datetime.fromisoformat(release_date.lstrip("+")).date()
    except ValueError:
        print(f"Invalid release date: '{release_date}'")
        return None
    

def parse_duration(duration: str) -> timedelta:
    try:
        minutes = round(float(duration.lstrip("+")))
    except ValueError:
        print(f"Invalid duration: '{duration}'")
        minutes = 0
    return timedelta(minutes=minutes)


def import_movies() -> None:
    file_path = settings.BASE_DIR.parent / "movies.json"
    with open(file_path, "r") as json_file:
        movies_json = json.load(json_file)

    count = 0

    for movie_id, movie_data in movies_json.items():
        movie_title = movie_data["labels"]["en"]
        print(count, movie_title) 

        movie = Movie.objects.get_or_create(wikidata_id=movie_id)[0]
        movie.english_title = movie_title
        movie.description = movie_data["descriptions"]["en"]
        movie.release_date = parse_release_date(movie_data["date"])
        movie.duration = parse_duration(movie_data["duration"])

        for actor_name in movie_data["starring"].split(","):
            actor = Actor.objects.get_or_create(
                name=actor_name
            )[0]
            movie.cast.add(actor)

        for lang, lang_title in movie_data["labels"].items():
            if lang_title == movie.english_title:
                continue

            # Include only macrolanguages
            if "-" in lang:
                continue

            alternative_movie_title = AlternativeMovieTitle.objects.get_or_create(
                movie=movie, 
                language_code=lang
            )[0]
            alternative_movie_title.title = lang_title
            alternative_movie_title.save()


        movie.save()

        count += 1
