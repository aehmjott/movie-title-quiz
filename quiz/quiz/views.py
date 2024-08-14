from django import views
from django.shortcuts import render
from django.db.models import Count

from movies.models import Movie, AlternativeMovieTitle


class IndexView(views.View):

    def get(self, request):

        # Get titles that differenciate enough from the english version
        # but not too much to ensure a fair experience
        titles = AlternativeMovieTitle.objects.filter(
            translation_difference_ratio__gte=0.25,
            translation_difference_ratio__lt=0.75,
        )

        # Pick out a random movie from these titles
        movie = titles.order_by("?").first().movie

        # Pick up to 3 titles for the quiz
        titles = titles.filter(movie=movie).order_by("?")[:3]

        return render(
            request,
            "index.html",
            {"movie": movie, "alternative_titles": titles},
        )
