import csv
import django
import os
import re

# Настроим Django перед импортом моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Artist, Painting  # Импортируем модели

# Путь к CSV-файлу (замени на свой)
CSV_FILE = "../classes.csv"

def extract_year(description):
    """
    Извлекает год из описания картины.
    Если в описании присутствует строка "not_detected", возвращает None.
    Иначе ищет все 4-значные числа и возвращает последнее найденное.
    """
    if "not_detected" in description:
        return None
    matches = re.findall(r'(\d{4})', description)
    if matches:
        return int(matches[-1])
    return None

def import_paintings(csv_file):
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row['filename']
            artist_name = row['artist'].strip().lower()  # Приводим к нижнему регистру
            genre = row['genre']
            description = row['description']
            width = int(row['width']) if row['width'] else None
            height = int(row['height']) if row['height'] else None
            genre_count = int(row['genre_count']) if row['genre_count'] else None

            # Определяем год написания картины по описанию
            year = extract_year(description)

            # Проверяем, есть ли художник в базе (без учёта регистра)
            artist = Artist.objects.filter(name__iexact=artist_name).first()
            if artist is None:
                print(f"Skipping {filename}: artist '{artist_name}' not found.")
                continue  # Пропускаем эту картину

            # Если художник найден, создаём или обновляем картину
            painting, created = Painting.objects.update_or_create(
                filename=filename,
                defaults={
                    'artist': artist,
                    'genre': genre,
                    'name': description,
                    'width': width,
                    'height': height,
                    'genre_count': genre_count,
                    'year': year  # Сохраняем год написания
                }
            )
            if created:
                print(f"Painting created: {painting.filename} (Artist ID: {artist.id}, Year: {year})")
            else:
                print(f"Painting updated: {painting.filename} (Artist ID: {artist.id}, Year: {year})")

    # Обновляем количество картин у каждого художника
    update_artist_painting_counts()

def update_artist_painting_counts():
    """ Пересчитывает количество картин у каждого художника """
    for artist in Artist.objects.all():
        count = Painting.objects.filter(artist=artist).count()
        artist.paintings = count
        artist.save()
        print(f"Updated artist {artist.name}: {count} paintings")

if __name__ == "__main__":
    import_paintings(CSV_FILE)
