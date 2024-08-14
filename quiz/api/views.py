from rest_framework import permissions, viewsets

from movies.models import Movie
from .serializers import MovieSerializer


class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    # TODO: Optimize queryset and remove slice operator
    queryset = (
        Movie.objects.all()
        .order_by("-sitelinks")
        .prefetch_related("alternative_titles")
    )[:10]
    serializer_class = MovieSerializer
    permission_classes = [permissions.IsAuthenticated]


class QuestionView:
    pass
