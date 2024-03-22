import requests
import json
import time

def send_request(url, params={}):
    response = requests.get(url, params=params)
    if response.status_code != 200:
        raise Exception("Error: " + str(response.status_code))
    response_json = response.json()
    if "error" in response_json:
        raise Exception(response_json["error"]["info"])
    return response_json


def flatten_dict(d):
    return {key: value["value"] for (key, value) in d.items()}


def send_wikidata_request(ids=[], extra_props=[], language=None):
    params = {
        "action": "wbgetentities",
        "ids": "|".join(ids),
        "props": "|".join(["labels", "descriptions"] + extra_props),
        "format": "json"
    }

    if language is not None:
        params["languages"] = language
        params["languagefallback"] = "true"

    response = send_request("https://www.wikidata.org/w/api.php", params)

    return response["entities"]

def get_movie_data(movie_ids):
    movie_list = send_wikidata_request(movie_ids, extra_props=["claims"])

    result =  {}
    for movie_id, movie_data in movie_list.items():
        labels = flatten_dict(movie_data["labels"])
        print(labels.get("en", "???"))
        movie = {
            "labels": labels,
            "descriptions": flatten_dict(movie_data["descriptions"]),
            "country": get_claim_values(movie_data, "P495", limit=1),
            "date": get_claim_values(movie_data, "P577", limit=1),
            "director": get_claim_values(movie_data, "P57", limit=3),
            "duration": get_claim_values(movie_data, "P2047", limit=1),
            "starring": get_claim_values(movie_data, "P161|P725", limit=5), # cast members & voice actors
        }
        
        result[movie_id] = movie
    return result


def get_claim_values(movie_data, claim_ids, limit=10):

    values = []
    claim_value_ids = []

    for claim_id in claim_ids.split("|"):
        if claim_id in movie_data["claims"]:
            
            claims = movie_data["claims"][claim_id][:limit]

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
        response = send_wikidata_request(claim_value_ids, language="en")
        values += [d["labels"]["en"]["value"] for d in response.values()]

    return ",".join(values)


def main ():

    with open("query.json", "r") as json_file:
        wikidata_links = json.load(json_file)
    wikidata_ids = [l["q"].split("/")[-1] for l in wikidata_links]

    # wikidata_ids = wikidata_ids[:10]
    
    try:
        with open("movies.json", "r") as json_file:
            movies_json = json.load(json_file)
    except FileNotFoundError:
        movies_json = {}

    for i in range(0, len(wikidata_ids), 50):
        movies_json |= get_movie_data(wikidata_ids[i:i+50])
        print(len(movies_json))
        time.sleep(1)

    with open("movies.json", "w") as json_file:
        json.dump(movies_json, json_file, indent=4)
    
if __name__ == "__main__":
    main()