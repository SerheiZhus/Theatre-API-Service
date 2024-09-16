from django.contrib import admin
from .models import (
    Actor, Genre, Play, TheatreHall,
    Performance, Reservation, Ticket
)

class TicketInline(admin.TabularInline):
    model = Ticket
    extra = 1

class ReservationAdmin(admin.ModelAdmin):
    inlines = (TicketInline,)


admin.site.register(Actor)
admin.site.register(Genre)
admin.site.register(Play)
admin.site.register(TheatreHall)
admin.site.register(Performance)
admin.site.register(Reservation, ReservationAdmin)
admin.site.register(Ticket)