
from rest_framework import serializers
from theatre.models import (
    Genre,
    Actor,
    Play,
)


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class PlaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres")


class PlayListSerializer(serializers.ModelSerializer):
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    genres = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="name"
    )

    class Meta:
        model = Play
        fields = ("id", "title", "actors", "genres")