# Movie Title Quiz

A Django application to play a fun movie quiz.

## Setup

```bash
pip install -r requirements.txt

cp .env.template .env
# Create a secret key and add to .env
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'

python manage.py migrate

python manage.py createsuperuser

python manage.py runserver
```

## How do I add movies?
### 1. Wikidata Import
`python manage.py import_wikidata COUNT`

Imports the `COUNT` most "popular" movies from Wikidata according to their sitelink count.
Repeat this command to download `COUNT` more movies.
For now only Wikidata-ID and the number of sitelinks are imported.


### 2. Wikidata Detail Import
`python manage.py import_wikidata_details`

Populate the movies created in step one with information from Wikidata:
- English movie title
- English description
- Non-English movie titles
- Director
- Actors
- Runtime
- Release Date

### 3. Movie Title Translation
`python manage.py translate_movie_titles`
Translates the foreign movie titles into English with MarianMT