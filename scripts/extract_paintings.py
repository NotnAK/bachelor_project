import os
import django
import zipfile

# Configure Django before importing models
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Paths
ZIP_PATH = r"C:\Users\Anton\Downloads\archive.zip"  # Provide your .zip file path
EXTRACT_FOLDER = r"C:\Users\Anton\Downloads\extracted_paintings"  # Where to extract

def extract_valid_paintings(zip_path, extract_folder):
    """Extracts only files that exist in the database from the archive, after user confirmation."""

    # Get a set of filenames from the database (no archive paths)
    existing_files = set(Painting.objects.values_list("filename", flat=True))
    print(f"Found {len(existing_files)} files in the database.")

    # Open the zip archive
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # List all files in the archive
        all_files = zip_ref.namelist()

        # Normalize archive paths to database format (replace backslashes with forward slashes)
        valid_files = [file for file in all_files if file.replace("\\", "/") in existing_files]

        print(f"Will extract: {len(valid_files)} files")

        # Show first 10 files as examples
        print("\nSample files to be extracted:")
        for file in valid_files[:10]:
            print(f"  {file}")

        # Ask for user confirmation
        confirm = input("\nContinue extraction? (y/n): ").strip().lower()
        if confirm != "y":
            print("Extraction cancelled.")
            return

        # Create the folder if it doesn’t exist
        os.makedirs(extract_folder, exist_ok=True)

        # Extract only the valid files
        for file in valid_files:
            zip_ref.extract(file, extract_folder)
            print(f"Extracted: {file}")

        print("Extraction completed!")

if __name__ == "__main__":
    extract_valid_paintings(ZIP_PATH, EXTRACT_FOLDER)
