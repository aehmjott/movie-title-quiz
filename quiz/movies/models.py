from django.db import models
from datetime import timedelta

from django.utils.translation import gettext_lazy as _


class Actor(models.Model):

    wikidata_id = models.CharField(max_length=20)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Movie(models.Model):

    wikidata_id = models.CharField(max_length=20, unique=True)
    sitelinks = models.IntegerField(default=0)

    english_title = models.CharField(max_length=250)
    description = models.TextField(blank=True)
    release_date = models.DateField(null=True, blank=True)
    cast = models.ManyToManyField(Actor, related_name="movies", blank=True)
    duration = models.DurationField(default=timedelta(minutes=0))

    def __str__(self):
        return self.english_title


class AlternativeMovieTitle(models.Model):

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    title = models.CharField(max_length=250)
    translated_title = models.CharField(max_length=250, blank=True)
    language_code = models.CharField(max_length=10)

    def __str__(self):
        return f"{self.title} ({self.language_code};{self.movie.english_title})"
