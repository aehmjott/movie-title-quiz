from rest_framework import serializers
from movies.models import Movie, AlternativeMovieTitle


class AlternativeMovieTitleSerializer(serializers.HyperlinkedModelSerializer):

    class Meta:
        model = AlternativeMovieTitle
        fields = [
            "title",
            "language_code",
            "translated_title",
            "translation_difference_ratio",
        ]


class MovieSerializer(serializers.HyperlinkedModelSerializer):

    alternative_titles = AlternativeMovieTitleSerializer(many=True, read_only=True)

    class Meta:
        model = Movie
        fields = ["english_title", "sitelinks", "alternative_titles"]
