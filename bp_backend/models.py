from django.db import models
from pgvector.django import VectorField

class Artist(models.Model):
    artist_id = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=255)
    years = models.CharField(max_length=100, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    nationality = models.CharField(max_length=100, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    wikipedia = models.URLField(blank=True, null=True)
    paintings = models.IntegerField(blank=True, null=True)

    def __str__(self):
        return self.name

class Painting(models.Model):
    filename = models.CharField(max_length=255)
    artist = models.ForeignKey(Artist, on_delete=models.SET_NULL, blank=True, null=True)
    genre = models.CharField(max_length=100, blank=True, null=True)
    name = models.TextField(blank=True, null=True)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    genre_count = models.IntegerField(blank=True, null=True)
    year = models.IntegerField(blank=True, null=True)
    embedding = VectorField(dimensions=768, blank=True, null=True)
    detailed_caption = models.TextField(blank=True, null=True)
    caption_embedding = VectorField(dimensions=768, blank=True, null=True) 
    def __str__(self):
        return self.filename
