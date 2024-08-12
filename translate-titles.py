import json
from transformers import MarianMTModel, MarianTokenizer

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
        "hy": "hy",
        "to": "to",
    }

def main ():
    with open("movies.json", "r") as json_file:
        movies_json = json.load(json_file)
        
    translated_movies = {}
    
    for movie_id, movie_data in movies_json.items():
        mov = {}
        mov["title"] = movie_data["labels"]["en"]
        mov["description"] = movie_data["descriptions"]["en"]
        mov["date"] = movie_data["date"]
        mov["starring"] = movie_data["starring"]
        mov["duration"] = movie_data["duration"]
        mov["labels"] = {}
        
        translated_movies[movie_id] = mov
    
    count = 0
    
    titles_by_language = {}
    
    for movie_id, movie_data in movies_json.items():
        
        if count > 10:
            break
    
        movie_data = movie_data.copy()
        title_eng = movie_data["labels"].get("en", None)
        if title_eng is None:
            continue
        for lang, lang_title in movie_data["labels"].items():
            
            if lang_title == title_eng:
                continue

            if lang in titles_by_language:
                titles_by_language[lang] += [(movie_id, lang_title)]
            else:
                titles_by_language[lang] = [(movie_id, lang_title)]
                
        count += 1
                
    for lang, movies in titles_by_language.items():
        
        if lang not in LANGUAGE_MAP:
            continue
    
        movie_ids, movie_titles = zip(*movies)
        
        print(lang)
           
        model_name = f"Helsinki-NLP/opus-mt-{LANGUAGE_MAP[lang]}-en"
        
        # Translate one language at a time
        tokenizer = MarianTokenizer.from_pretrained(model_name, source_lang=lang, target_lang="en", clean_up_tokenization_spaces=True)
        model = MarianMTModel.from_pretrained(model_name)
        
        tokens = tokenizer(movie_titles, return_tensors="pt", padding=True)
        translated = model.generate(**tokens)
        translated_titles = [tokenizer.decode(t, skip_special_tokens=True) for t in translated]
        
        print(movie_ids)
        print(movie_titles)
        print(translated_titles)
        
        for idx, movie_id in enumerate(movie_ids):
            
            translated_movies[movie_id]["labels"][lang] = {
                "original": movie_titles[idx],
                "translated": translated_titles[idx]
            }
            
    with open("movies-translated2.json", "w") as json_file:
        json.dump(translated_movies, json_file, indent=4)
            
if __name__ == "__main__":
    main()