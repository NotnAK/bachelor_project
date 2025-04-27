from django.db import models
from pgvector.django import VectorField  # <-- важно

class Artist(models.Model):
    artist_id = models.IntegerField(blank=True, null=True)  # поле из CSV (id)
    name = models.CharField(max_length=255)
    years = models.CharField(max_length=100, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wikipedia = models.URLField(blank=True, null=True)
    paintings = models.IntegerField(blank=True, null=True)  # кол-во картин

    def __str__(self):
        return self.name

class Painting(models.Model):
    filename = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    phash = models.CharField(max_length=64, blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    genre_count = models.IntegerField(blank=True, null=True)
    subset = models.CharField(max_length=50, blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)  # Новое поле с годом написания
    # Новое поле: вектор эмбеддингов (768 - пример, зависит от модели Florence)
    embedding = VectorField(dimensions=512, blank=True, null=True)
    detailed_caption = models.TextField(blank=True, null=True)  # новое поле для Florence‑2 сгенерированного описания
    def __str__(self):
        return self.filename
