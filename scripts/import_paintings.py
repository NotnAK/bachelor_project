import csv
import django
import os
import re

# Configure Django before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Artist, Painting  # Import models

# Path to the CSV file (replace with your own)
CSV_FILE = "../classes.csv"

def extract_year(description):
    """
    Extracts a year from the painting description.
    If the description contains "not_detected", returns None.
    Otherwise, finds all 4-digit numbers and returns the last one found.
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
            artist_name = row['artist'].strip().lower()  # Convert to lowercase
            genre = row['genre']
            description = row['description']
            width = int(row['width']) if row['width'] else None
            height = int(row['height']) if row['height'] else None
            genre_count = int(row['genre_count']) if row['genre_count'] else None

            # Determine painting year from description
            year = extract_year(description)

            # Check if artist exists in the database (case-insensitive)
            artist = Artist.objects.filter(name__iexact=artist_name).first()
            if artist is None:
                print(f"Skipping {filename}: artist '{artist_name}' not found.")
                continue  # Skip this painting

            # If artist is found, create or update the painting
            painting, created = Painting.objects.update_or_create(
                filename=filename,
                defaults={
                    'artist': artist,
                    'genre': genre,
                    'name': description,
                    'width': width,
                    'height': height,
                    'genre_count': genre_count,
                    'year': year  # Save the painting year
                }
            )
            if created:
                print(f"Painting created: {painting.filename} (Artist ID: {artist.id}, Year: {year})")
            else:
                print(f"Painting updated: {painting.filename} (Artist ID: {artist.id}, Year: {year})")

    # Update the number of paintings for each artist
    update_artist_painting_counts()

def update_artist_painting_counts():
    """Recalculates the number of paintings for each artist."""
    for artist in Artist.objects.all():
        count = Painting.objects.filter(artist=artist).count()
        artist.paintings = count
        artist.save()
        print(f"Updated artist {artist.name}: {count} paintings")

if __name__ == "__main__":
    import_paintings(CSV_FILE)
