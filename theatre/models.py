from django.conf import settings
from django.db import models


class Actor(models.Model):
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.first_name + " " + self.last_name

    @property
    def full_name(self) -> str:
        return f"{self.first_name} {self.last_name}"


class Genre(models.Model):
    name = models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.name

class Play(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    actors = models.ManyToManyField(Actor, blank=True)
    genres = models.ManyToManyField(Genre, blank=True)

    class Meta:
        ordering = ["title"]

    def __str__(self) -> str:
        return self.title


