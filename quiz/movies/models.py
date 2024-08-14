from django.db import models
from datetime import timedelta
from difflib import SequenceMatcher

from django.utils.translation import gettext_lazy as _


class Person(models.Model):

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
    cast = models.ManyToManyField(Person, related_name="acting_credits", blank=True)
    directed_by = models.ManyToManyField(
        Person, related_name="direction_credits", blank=True
    )
    duration = models.DurationField(default=timedelta(minutes=0))

    def __str__(self):
        return self.english_title


class AlternativeMovieTitle(models.Model):

    movie = models.ForeignKey(
        Movie, on_delete=models.CASCADE, related_name="alternative_titles"
    )
    title = models.CharField(max_length=250)
    translated_title = models.CharField(max_length=250, blank=True)
    language_code = models.CharField(max_length=10)
    translation_difference_ratio = models.FloatField(default=1.0)

    def normalize_titles(self):
        """
        Normalize movie titles to account for common machine translation mistakes
        """
        original = self.movie.english_title.lower()
        translation = self.translated_title.lower()

        if not original.endswith("."):
            translation = translation.rstrip(".")

        return original, translation

    def update_translation_difference_ratio(self):
        self.translation_difference_ratio = round(
            SequenceMatcher(None, *self.normalize_titles()).quick_ratio(),
            3,
        )

    def save(self, *args, **kwargs):
        self.update_translation_difference_ratio()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.title} ({self.language_code};{self.movie.english_title})"
