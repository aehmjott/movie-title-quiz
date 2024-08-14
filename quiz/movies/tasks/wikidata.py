from datetime import timedelta, datetime, date

from django.utils.http import urlencode

from movies.models import Person, Movie, AlternativeMovieTitle

import requests
import time


# Wikidata allows a maximum of 50 values per filter
MOVIES_PER_QUERY = 50


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


class WikidataGraphAPI:
    """
    Create basic ``Movie`` objects via SPARQL querys
    """

    def get_movies(self, offset: int, limit: int) -> list[dict]:
        """
        Send a request to Wikidata and return the entries
        """

        print(f"Querying wikidata: offset={offset}, limit={limit}")

        # Get the most popular movies on wikidata ("popular": has many sitelinks)
        sparql_query = """
        SELECT ?q ?sitelinks
        WHERE {{?q wdt:P31 wd:Q11424. ?q wikibase:sitelinks ?sitelinks.}}
        ORDER BY desc(?sitelinks)
        LIMIT {limit}
        OFFSET {offset}
        """.format(
            limit=limit, offset=offset
        )

        wikidata_url = f"https://query.wikidata.org/sparql?" + urlencode(
            {"query": sparql_query, "format": "json"}
        )

        response = requests.get(wikidata_url)
        result = response.json()["results"]["bindings"]
        return result

    def run(self, count: int) -> None:
        """
        Create ``count`` more Movie objects
        """

        # Never request more than 500 entries at once
        MAX_QUERY_LIMIT = 500

        print(f"Start wikidata download. count={count}")

        movie_data = []

        existing_count = Movie.objects.all().count()
        target_total = existing_count + count

        offset = existing_count
        while offset < target_total:
            limit = min(MAX_QUERY_LIMIT, target_total - offset)
            movie_data += self.get_movies(offset, limit)
            offset += limit

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
    """
    Use the wikidata REST API to update movie objects
    that were created with ``WikidataSparqlAPI``
    """

    def __init__(self, movies):
        self.movies = movies

    def send_request(self, url, params={}):
        response = requests.get(url, params=params)
        if response.status_code != 200:
            raise Exception("Error: " + str(response.status_code))
        response_json = response.json()
        if "error" in response_json:
            raise Exception(response_json["error"]["info"])
        return response_json

    def get_propertys_for_ids(self, ids=[], extra_props=[], language=None):
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
    ) -> list[str | timedelta | date | dict]:
        """
        Read property values from `movie_data` and return them as a list.
        Properties that refer to other Wikidata pages (e.g., Director)
        are fetched with a separate API request.
        """

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
                        values.append(parse_duration(claim["amount"]))
                    elif "time" in claim:
                        values.append(parse_release_date(claim["time"]))

        # Use the ids to get more details about these entries
        if claim_value_ids:
            response = self.get_propertys_for_ids(claim_value_ids, language="en")
            for d in response.values():
                label = d["labels"]["en"]["value"]
                if label_only:
                    values.append(label)
                else:
                    values.append({"id": d["id"], "label": label})
        return values

    def get_movie_data(self, movie_ids: list[str]) -> dict:
        """
        Get information about movies
        """
        movie_list = self.get_propertys_for_ids(movie_ids, extra_props=["claims"])

        result = {}
        for movie_id, movie_data in movie_list.items():
            result[movie_id] = {
                "labels": movie_data["labels"],
                "description": movie_data["descriptions"]["en"]["value"],
                "country": self.get_property_values(movie_data, "P495", limit=1)[0],
                "date": self.get_property_values(movie_data, "P577", limit=1)[0],
                "directors": self.get_property_values(
                    movie_data, "P57", limit=3, label_only=False
                ),
                "duration": self.get_property_values(movie_data, "P2047", limit=1)[0],
                "cast": self.get_property_values(
                    movie_data, "P161|P725", limit=5, label_only=False
                ),  # cast members & voice actors
            }
        return result

    def run(self) -> None:
        movie_count = self.movies.count()

        for i in range(0, movie_count, MOVIES_PER_QUERY):
            print(f"Downloading... {i}-{i+MOVIES_PER_QUERY}/{movie_count}")

            batch = self.movies[i : i + MOVIES_PER_QUERY]
            alternative_title_objects = []
            person_objects = []

            movies_json = self.get_movie_data([m.wikidata_id for m in batch])
            for movie in batch:
                movie_data = movies_json.get(movie.wikidata_id, None)
                if movie_data is None:
                    print("Error! Movie not found")
                    continue

                english_title = movie_data["labels"]["en"]["value"]
                print(f"Updating movie: {english_title}")

                movie.english_title = english_title
                movie.description = movie_data["description"]
                movie.release_date = movie_data["date"]
                movie.duration = movie_data["duration"]

                for actor in movie_data["cast"]:
                    actor_object = Person.objects.get_or_create(
                        wikidata_id=actor["id"]
                    )[0]
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
                    # Exclude country-specific titles and the ones that don't differ from the English version
                    if (
                        alternative_title == movie.english_title
                        or "-" in alternative_title["language"]
                    ):
                        continue

                    title_object, created = AlternativeMovieTitle.objects.get_or_create(
                        movie=movie,
                        language_code=alternative_title["language"],
                    )
                    title_object.title = alternative_title["value"]
                    title_object.translated_title = ""
                    alternative_title_objects.append(title_object)

            # Bulk update database objects
            Person.objects.bulk_update(person_objects, ["name"])

            AlternativeMovieTitle.objects.bulk_update(
                alternative_title_objects, ["title"]
            )

            Movie.objects.bulk_update(
                batch, ["english_title", "description", "release_date", "duration"]
            )

            time.sleep(1)
