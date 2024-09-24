from django.db.models import Count, F
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import mixins, viewsets, status
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from theatre.models import Genre, Actor, Play, TheatreHall, Performance, Reservation
from theatre.serializers import (
    ActorSerializer,
    GenreSerializer,
    PlaySerializer,
    PlayListSerializer,
    PlayRetrieveSerializer,
    TheatreHallSerializer,
    PerformanceSerializer,
    PerformanceListSerializer,
    PerformanceRetrieveSerializer,
    ReservationSerializer,
    ReservationListSerializer,
    PlayImageSerializer,
)


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


class TheatreHallViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    queryset = TheatreHall.objects.all()
    serializer_class = TheatreHallSerializer


class PlayViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = Play.objects.prefetch_related("actors", "genres")

    @staticmethod
    def _params_to_ints(qs):
        """Converts a list of string IDs to a list of integers"""
        return [int(str_id) for str_id in qs.split(",")]

    def get_serializer_class(self):
        """Returns the serializer class depending on the action ViewSet."""
        if self.action == "list":
            return PlayListSerializer
        elif self.action == "retrieve":
            return PlayRetrieveSerializer
        elif self.action == "upload_image":
            return PlayImageSerializer
        return PlaySerializer

    def get_queryset(self):
        """Retrieve the movies with filters"""
        title = self.request.query_params.get("title")
        actors = self.request.query_params.get("actors")
        genres = self.request.query_params.get("genres")

        queryset = self.queryset

        if title:
            queryset = queryset.filter(title__icontains=title)
        if actors:
            actor_ids = self._params_to_ints(actors)
            queryset = queryset.filter(actors__id__in=actor_ids)
        if genres:
            genre_ids = self._params_to_ints(genres)
            queryset = queryset.filter(genres__id__in=genre_ids)

        if self.action in ("list", "retrieve"):
            return queryset.prefetch_related("actors", "genres")

        return queryset.distinct()

    @action(
        detail=True,
        methods=["POST"],
        url_path="upload-image",
        permission_classes=(IsAdminUser,),
    )
    def upload_image(self, request, pk=None):
        """Endpoint for uploading image to specific movie"""
        play = self.get_object()
        serializer = self.get_serializer(
            play,
            data=request.data,
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                "genres",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by genre id (ex. ?genres=2,5)",
            ),
            OpenApiParameter(
                "actors",
                type={"type": "list", "items": {"type": "number"}},
                description="Filter by actor id (ex. ?actors=2,5)",
            ),
            OpenApiParameter(
                "title",
                type=OpenApiTypes.STR,
                description="Filter by movie title (ex. ?title=fiction)",
            ),
        ]
    )
    def list(self, request, *args, **kwargs):
        """Processes the request to obtain a list of objects"""
        return super().list(request, *args, **kwargs)


class PerformanceSetPagination(PageNumberPagination):
    page_size = 3
    page_size_query_param = "page_size"
    max_page_size = 20


class PerformanceViewSet(viewsets.ModelViewSet):
    queryset = Performance.objects.select_related("play", "theatre_hall")

    def get_serializer_class(self):
        """Returns the serializer class depending on the action ViewSet."""
        if self.action == "list":
            return PerformanceListSerializer
        elif self.action == "retrieve":
            return PerformanceRetrieveSerializer
        return PerformanceSerializer

    def get_queryset(self):
        """Returns a set of queries filtered and annotated according to the action"""
        queryset = self.queryset
        if self.action in "list":
            queryset = queryset.select_related("play", "theatre_hall").annotate(
                ticket_available=F("theatre_hall__rows")
                * F("theatre_hall__seats_in_row")
                - Count("tickets")
            )
        elif self.action in "retrieve":
            queryset = queryset.select_related("play", "theatre_hall")
        return queryset.order_by("id")


class ReservationViewSet(
    mixins.ListModelMixin, mixins.CreateModelMixin, GenericViewSet
):
    queryset = Reservation.objects.all()
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """Return a set of queries filtered by the` field and, if necessary,
        loading associated objects through the`prefetch_related."""
        queryset = self.queryset.filter(user=self.request.user)
        if self.action in "list":
            queryset = queryset.prefetch_related("tickets__performance__theatre_hall")
        return queryset

    def perform_create(self, serializer):
        """Saves a new object by associating it with the current user"""
        serializer.save(user=self.request.user)

    def get_serializer_class(self):
        """Returns the serializer class depending on the action ViewSet."""
        if self.action == "list":
            return ReservationListSerializer
        return ReservationSerializer
