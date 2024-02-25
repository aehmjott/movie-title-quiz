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

def get_movie_data(movie_ids):
    movie_data = send_request("https://www.wikidata.org/w/api.php", {
        "action": "wbgetentities", 
        "ids": "|".join(movie_ids), 
        "format":"json", 
        "props":"labels"
    })
    return movie_data["entities"]

def main ():

    with open("query.json", "r") as json_file:
        wikidata_links = json.load(json_file)
    wikidata_ids = [l["q"].split("/")[-1] for l in wikidata_links]
    
    try:
        with open("movies.json", "r") as json_file:
            movies_json = json.load(json_file)
    except FileNotFoundError:
        movies_json = []

    for i in range(0, len(wikidata_ids), 20):
        movies_json |= get_movie_data(wikidata_ids[i:i+20])
        print(len(movies_json))
        time.sleep(2)

    with open("movies.json", "w") as json_file:
        json.dump(movies_json, json_file)
    
if __name__ == "__main__":
    main()