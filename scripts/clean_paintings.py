import os
import django

# Configure Django before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Specify path to the folder with paintings
PAINTINGS_FOLDER = r"C:\Users\Anton\Downloads\archive"  # Provide the actual path

def clean_paintings(folder):
    """Deletes files that are not present in the database."""
    # Get a set of all filenames in the database
    existing_files = set(Painting.objects.values_list("filename", flat=True))

    # Walk through all files in the folder and its subdirectories
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)

            # If this is a file and it’s not in the database, delete it
            if os.path.isfile(file_path) and file not in existing_files:
                print(f"Deleting {file_path}")
                os.remove(file_path)

if __name__ == "__main__":
    clean_paintings(PAINTINGS_FOLDER)
