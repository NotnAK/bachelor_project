from django.contrib import admin
from django.urls import path
from .views import florence_inference

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/florence/', florence_inference),  # Новый эндпоинт для Florence-2
]
