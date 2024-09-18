from django.db import transaction
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from theatre.models import (
    Genre, Actor, Play,
    TheatreHall, Performance,
    Ticket, Reservation,
)


class GenreSerializer(serializers.ModelSerializer):

    class Meta:
        model = Genre
        fields = ("id", "name")


class ActorSerializer(serializers.ModelSerializer):

    class Meta:
        model = Actor
        fields = ("id", "first_name", "last_name", "full_name")


class TheatreHallSerializer(serializers.ModelSerializer):

    class Meta:
        model = TheatreHall
        fields = ("id", "name", "rows", "seats_in_row", "capacity")


class PlaySerializer(serializers.ModelSerializer):

    class Meta:
        model = Play
        fields = ("id", "title", "description", "actors", "genres")


class PlayListSerializer(PlaySerializer):
    actors = serializers.SlugRelatedField(
        many=True, read_only=True, slug_field="full_name"
    )
    genres = serializers.SlugRelatedField(many=True, read_only=True, slug_field="name")


class PlayRetrieveSerializer(PlaySerializer):
    actors = ActorSerializer(many=True)
    genres = GenreSerializer(many=True)



class PerformanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Performance
        fields = ("id", "play", "theatre_hall", "show_time")


class PerformanceListSerializer(PerformanceSerializer):
    play_title = serializers.CharField(source="play.title", read_only=True)
    theatre_hall_name = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
    total_seats = serializers.IntegerField(source="theatre_hall.capacity", read_only=True)
    ticket_available = serializers.IntegerField(read_only=True)

    class Meta:
        model = Performance
        fields = ("id", "play_title", "theatre_hall_name", "show_time", "total_seats", "ticket_available")



class TicketSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ticket
        fields = ("id", "row", "seat", "performance")

    def validate(self, attrs):
        data = super(TicketSerializer, self).validate(attrs=attrs)
        Ticket.validate_ticket(
            attrs["row"],
            attrs["seat"],
            attrs["performance"].theatre_hall,
            ValidationError
        )
        return data

class TicketListSerializer(TicketSerializer):
    performance = serializers.CharField(source="performance.play", read_only=True)


class TicketRetrieveSerializer(TicketSerializer):
    performance = PerformanceListSerializer(many=False, read_only=True)


class TicketSeatsSerializer(TicketSerializer):
    class Meta:
        model = Ticket
        fields = ("row", "seat")

class PerformanceRetrieveSerializer(PerformanceSerializer):
    play = PlayListSerializer()
    theatre_hall = serializers.CharField(
        source="theatre_hall.name", read_only=True
    )
    ticket_taken = TicketSeatsSerializer(many=True, read_only=True, source="tickets")

    class Meta:
        model = Performance
        fields = ("id", "play", "show_time","theatre_hall", "ticket_taken",)




class ReservationSerializer(serializers.ModelSerializer):
    tickets = TicketSerializer(many=True, read_only=False, allow_empty=False)

    class Meta:
        model = Reservation
        fields = ("id", "created_at", "tickets")

    def create(self, validated_data):
        with transaction.atomic():
            tickets_data = validated_data.pop("tickets")
            reservation = Reservation.objects.create(**validated_data)
            for ticket_data in tickets_data:
                Ticket.objects.create(reservation=reservation, **ticket_data)
            return reservation


class ReservationListSerializer(ReservationSerializer):
    tickets = TicketListSerializer(many=True, read_only=True)


class ReservationRetrieveSerializer(ReservationSerializer):
    tickets = TicketRetrieveSerializer(many=True, read_only=True)
