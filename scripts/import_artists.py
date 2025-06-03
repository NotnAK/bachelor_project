import csv
import django
import os

# Настроим Django перед импортом моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Artist

# Путь к CSV-файлу (замени на свой)
CSV_FILE = "../artists.csv"

def import_artists(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            artist_id = int(row['id']) if row['id'] else None
            name = row['name']
            years = row['years']
            genre = row['genre']
            nationality = row['nationality']
            bio = row['bio']
            wikipedia = row['wikipedia']
            paintings = int(row['paintings']) if row['paintings'] else None

            # Сохраняем в базу
            artist, created = Artist.objects.update_or_create(
                artist_id=artist_id,
                defaults={
                    'name': name,
                    'years': years,
                    'genre': genre,
                    'nationality': nationality,
                    'bio': bio,
                    'wikipedia': wikipedia,
                    'paintings': paintings
                }
            )
            if created:
                print(f"Создан: {artist.name}")
            else:
                print(f"Обновлён: {artist.name}")

if __name__ == "__main__":
    import_artists(CSV_FILE)
