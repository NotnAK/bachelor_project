from django.contrib import admin
from .models import Artist, Painting

@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    list_display = ("name", "nationality", "years", "paintings")
    search_fields = ("name", "nationality", "genre")
    list_filter = ("nationality", "genre")

@admin.register(Painting)
class PaintingAdmin(admin.ModelAdmin):
    list_display = ("filename", "artist", "genre", "width", "height")
    search_fields = ("filename", "genre")
    list_filter = ("genre", "subset")
