from transformers import MarianMTModel, MarianTokenizer
from collections import defaultdict

from movies.models import AlternativeMovieTitle

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

# Batches should be as large as possible,
# but a batch size that is too large may lead to crashes.
# 25 works fine on my machine
MAX_BATCH_SIZE = 25


class MovieTitleTranslator:

    def __init__(self, movie_titles):
        self.movie_titles = movie_titles

    def run(self):

        total_count = 0
        translated_count = 0

        # Group titles by language before translating to increase the batch size
        #
        titles_by_language = {}
        for title_obj in self.movie_titles:
            if title_obj.language_code in titles_by_language:
                batches = titles_by_language[title_obj.language_code]
                if len(batches[-1]) < MAX_BATCH_SIZE:
                    batches[-1].append(title_obj)
                else:
                    batches.append([title_obj])
            else:
                titles_by_language[title_obj.language_code] = [[title_obj]]
            total_count += 1

        print(f"Translating {total_count} movie titles")

        # Translate one language at a time
        for language_code, batches in titles_by_language.items():
            print(f"Translating language '{language_code}' Batches: {len(batches)}")

            # https://huggingface.co/docs/transformers/model_doc/marian
            model_name = f"Helsinki-NLP/opus-mt-{LANGUAGE_MAP[language_code]}-en"

            tokenizer = MarianTokenizer.from_pretrained(
                model_name,
                source_lang=language_code,
                target_lang="en",
                clean_up_tokenization_spaces=False,
            )
            model = MarianMTModel.from_pretrained(model_name)

            for movie_title_objects in batches:
                print(f"Batch size: {len(movie_title_objects)}")

                tokens = tokenizer(
                    [m.title for m in movie_title_objects],
                    return_tensors="pt",
                    padding=True,
                )
                translated = model.generate(**tokens)
                translated_titles = [
                    tokenizer.decode(t, skip_special_tokens=True) for t in translated
                ]

                # Update the AlternativeMovieTitle objects
                for title_obj, translated_title in zip(
                    movie_title_objects, translated_titles
                ):
                    title_obj.translated_title = translated_title
                    title_obj.update_translation_difference_ratio()

                AlternativeMovieTitle.objects.bulk_update(
                    movie_title_objects, ["translated_title"]
                )
                translated_count += len(movie_title_objects)
                print(f"{translated_count}/{total_count} done.")
