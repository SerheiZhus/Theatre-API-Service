
from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from theatre.models import Genre, Actor, Play
from theatre.serializers import ActorSerializer, GenreSerializer, PlaySerializer


class GenreViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer



class ActorViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = Actor.objects.all()
    serializer_class = ActorSerializer

class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Play.objects.prefetch_related("actors", "genres")
    serializer_class = PlaySerializer
