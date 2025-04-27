from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from bp_backend.views import search_similar_paintings
from bp_backend.views import (
    paintings_list,
    painting_detail,
    filter_options,
    search_similar_paintings_clip,
    search_similar_paintings_clip_1024,
    search_similar_paintings_clip_vqa
)
urlpatterns = [
    path('admin/', admin.site.urls),
    path('paintings/', paintings_list, name='paintings_list'),
    path('paintings/<int:pk>/', painting_detail, name='painting_detail'),
    path('filter-options/', filter_options, name='filter_options'),
    path('search_similar/', search_similar_paintings, name='search_similar_paintings'),
    path("search_similar_clip/", search_similar_paintings_clip, name="search_similar_clip"),
    path("search_similar_paintings_clip_vqa/", search_similar_paintings_clip_vqa, name="search_similar_paintings_clip_vqa"),
    path("search_similar_paintings_clip_1024/", search_similar_paintings_clip_1024, name="search_similar_paintings_clip_1024"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
