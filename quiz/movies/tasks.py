from collections import defaultdict
from datetime import timedelta, datetime, date
from transformers import MarianMTModel, MarianTokenizer

from django.conf import settings
from django.utils.http import urlencode

from .models import Person, Movie, AlternativeMovieTitle

import requests
import time


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


def wikidata_query(offset: int, limit: int):

    print(f"Querying wikidata: offset={offset}, limit={limit}]")

    # Get the most popular movies on wikidata ("popular": has many sitelinks)
    sparql_query = """
    SELECT ?q ?sitelinks
    WHERE {{?q wdt:P31 wd:Q11424. ?q wikibase:sitelinks ?sitelinks.}}
    ORDER BY desc(?sitelinks)
    LIMIT {count}
    OFFSET {offset}
    """.format(
        count=limit, offset=offset
    )

    wikidata_url = f"https://query.wikidata.org/sparql?" + urlencode(
        {"query": sparql_query, "format": "json"}
    )
    response = requests.get(wikidata_url)
    return response.json()["results"]["bindings"]


def wikidata_download(count: int, query_limit: int = 1000) -> None:
    """
    Create Movie objects from wikidata
    """

    print(f"Start wikidata download. count={count}, limit per query={query_limit}")

    movie_data = []

    offset = 0
    while offset + query_limit <= count:
        movie_data += wikidata_query(offset, query_limit)
        offset += query_limit

    print(f"Number of elements: {len(movie_data)}")

    movie_objects = []
    for m in movie_data:
        movie_id = m["q"]["value"].split("/")[-1]
        sitelinks = int(m["sitelinks"]["value"])
        movie_objects.append(Movie(wikidata_id=movie_id, sitelinks=sitelinks))

    Movie.objects.bulk_create(
        movie_objects,
        update_conflicts=True,
        unique_fields=["wikidata_id"],
        update_fields=["sitelinks"],
    )


class WikidataAPI:

    def send_request(self, url, params={}):
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception("Error: " + str(response.status_code))
        response_json = response.json()
        if "error" in response_json:
            raise Exception(response_json["error"]["info"])
        return response_json

    def send_wikidata_request(self, ids=[], extra_props=[], language=None):
        params = {
            "action": "wbgetentities",
            "ids": "|".join(ids),
            "props": "|".join(["labels", "descriptions"] + extra_props),
            "format": "json",
        }

        if language is not None:
            params["languages"] = language
            params["languagefallback"] = "true"

        response = self.send_request("https://www.wikidata.org/w/api.php", params)
        if "entities" not in response:
            print("Error! Missing entities in response")
            print(response.keys())
            return {}
        return response["entities"]

    def get_property_values(
        self,
        movie_data: dict,
        property_ids: str,
        limit: int = 10,
        label_only: bool = True,
    ):

        values = []
        claim_value_ids = []

        for property_id in property_ids.split("|"):
            if property_id in movie_data["claims"]:

                claims = movie_data["claims"][property_id][:limit]

                for claim in claims:
                    if "datavalue" not in claim["mainsnak"]:
                        continue
                    claim = claim["mainsnak"]["datavalue"]["value"]
                    if "id" in claim:
                        claim_value_ids.append(claim["id"])
                    elif "amount" in claim:
                        values.append(claim["amount"])
                    elif "time" in claim:
                        values.append(claim["time"])

        if claim_value_ids:
            response = self.send_wikidata_request(claim_value_ids, language="en")
            for d in response.values():
                label = d["labels"]["en"]["value"]
                if label_only:
                    values.append(label)
                else:
                    values.append({"id": d["id"], "label": label})
        return values

    def get_movie_data(self, movie_ids):
        movie_list = self.send_wikidata_request(movie_ids, extra_props=["claims"])

        result = {}
        for movie_id, movie_data in movie_list.items():
            result[movie_id] = {
                "labels": movie_data["labels"],
                "description": movie_data["descriptions"]["en"]["value"],
                "country": self.get_property_values(movie_data, "P495", limit=1),
                "date": self.get_property_values(movie_data, "P577", limit=1),
                "directors": self.get_property_values(
                    movie_data, "P57", limit=3, label_only=False
                ),
                "duration": self.get_property_values(movie_data, "P2047", limit=1),
                "cast": self.get_property_values(
                    movie_data, "P161|P725", limit=5, label_only=False
                ),  # cast members & voice actors
            }
        return result


def wikidata_detail_download():
    incomplete_movie_objects = Movie.objects.filter(english_title="")
    movie_count = incomplete_movie_objects.count()

    MOVIES_PER_QUERY = 50
    for i in range(0, movie_count, MOVIES_PER_QUERY):
        print(f"Downloading... {i}-{i+MOVIES_PER_QUERY}/{movie_count}")

        batch = incomplete_movie_objects[i : i + MOVIES_PER_QUERY]
        alternative_title_objects = []
        person_objects = []

        movies_json = WikidataAPI().get_movie_data([m.wikidata_id for m in batch])
        for movie in batch:
            movie_data = movies_json.get(movie.wikidata_id, None)
            if movie_data is None:
                print("Error! Movie not found")
                continue

            english_title = movie_data["labels"]["en"]["value"]
            print(f"Updating movie: {english_title}")

            movie.english_title = english_title
            movie.description = movie_data["description"]
            movie.release_date = parse_release_date(movie_data["date"][0])
            movie.duration = parse_duration(movie_data["duration"][0])

            for actor in movie_data["cast"]:
                actor_object = Person.objects.get_or_create(wikidata_id=actor["id"])[0]
                actor_object.name = actor["label"]
                person_objects.append(actor_object)
                movie.cast.add(actor_object)

            for director in movie_data["directors"]:
                director_object = Person.objects.get_or_create(
                    wikidata_id=director["id"]
                )[0]
                director_object.name = director["label"]
                person_objects.append(director_object)
                movie.directed_by.add(director_object)

            for alternative_title in movie_data["labels"].values():
                # Exclude titles that don't differ from the English title
                # or are country-specific (de-at, es-mx, ...)
                if (
                    alternative_title == movie.english_title
                    or "-" in alternative_title["language"]
                ):
                    continue
                title_object = AlternativeMovieTitle.objects.get_or_create(
                    movie=movie,
                    language_code=alternative_title["language"],
                )[0]
                title_object.title = alternative_title["value"]
                alternative_title_objects.append(title_object)

        Person.objects.bulk_update(person_objects, ["name"])

        AlternativeMovieTitle.objects.bulk_update(alternative_title_objects, ["title"])

        Movie.objects.bulk_update(
            batch, ["english_title", "description", "release_date", "duration"]
        )

        time.sleep(1)


# Map language codes to translation models
LANGUAGE_MAP = {
    "de": "de",
    "fr": "fr",
    "es": "es",
    "da": "da",
    "ru": "ru",
    "cs": "cs",
    "it": "it",
    "sv": "sv",
    "ro": "ROMANCE",
    "ja": "ja",
    "fi": "fi",
    "ka": "ka",
    "hi": "hi",
    "no": "da",
    "tr": "tr",
    "ko": "ko",
    "hu": "hu",
    "be": "mul",
    "zh": "zh",
    "ar": "ar",
    "pl": "pl",
    "nl": "nl",
    "th": "th",
    "sk": "sk",
    "is": "is",
    "nb": "gmq",
    "uk": "uk",
    "id": "id",
    "lv": "lv",
    "sq": "sq",
    "sw": "mul",
    "vi": "vi",
    "el": "grk",
    "et": "et",
    "to": "to",
}


def translate_movie_titles(limit: int = 1000):
    """
    Translate ``limit`` untranslated AlternativeMovieTitle objects intro English.

    Objects with a language code not defined in ``LANGUAGE_MAP```are ignored.
    """

    [m.save() for m in AlternativeMovieTitle.objects.all()]
    return

    total_count = 0
    translated_count = 0

    # Group titles by language
    titles_by_language = defaultdict(list)
    for title_obj in AlternativeMovieTitle.objects.filter(
        translated_title="", language_code__in=LANGUAGE_MAP.keys()
    ).exclude(movie__english_title="")[:limit]:
        titles_by_language[title_obj.language_code].append(title_obj)
        total_count += 1

    print(f"Translating {total_count} movie titles")

    # Translate one language at a time
    for language_code, movie_title_objects in titles_by_language.items():

        print(
            f"Translating language '{language_code}' titles: {len(movie_title_objects)}"
        )

        # https://huggingface.co/docs/transformers/model_doc/marian
        model_name = f"Helsinki-NLP/opus-mt-{LANGUAGE_MAP[language_code]}-en"

        tokenizer = MarianTokenizer.from_pretrained(
            model_name,
            source_lang=language_code,
            target_lang="en",
            clean_up_tokenization_spaces=True,
        )
        model = MarianMTModel.from_pretrained(model_name)

        movie_titles = [m.title for m in movie_title_objects]
        tokens = tokenizer(movie_titles, return_tensors="pt", padding=True)
        translated = model.generate(**tokens)
        translated_titles = [
            tokenizer.decode(t, skip_special_tokens=True) for t in translated
        ]

        # Update the AlternativeMovieTitle objects
        for title_obj, translated_title in zip(movie_title_objects, translated_titles):
            title_obj.translated_title = translated_title
            title_obj.update_translation_difference_ratio()

        AlternativeMovieTitle.objects.bulk_update(
            movie_title_objects, ["translated_title"]
        )
        translated_count += len(movie_title_objects)
        print(f"{translated_count}/{total_count} done.")
