import os
import django
import zipfile

# Настроим Django перед импортом моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Пути
ZIP_PATH = r"C:\Users\Антон\Downloads\archive.zip"  # Укажи свой .zip
EXTRACT_FOLDER = r"C:\Users\Антон\Downloads\extracted_paintings"  # Куда распаковывать

def extract_valid_paintings(zip_path, extract_folder):
    """Распаковывает из архива только файлы, которые есть в базе данных, после подтверждения пользователя"""

    # Получаем список файлов из базы данных (без пути к архиву)
    existing_files = set(Painting.objects.values_list("filename", flat=True))
    print(f"Найдено {len(existing_files)} файлов в базе данных.")

    # Открываем архив
    with zipfile.ZipFile(zip_path, "r") as zip_ref:
        # Получаем список файлов в архиве
        all_files = zip_ref.namelist()

        # Приводим пути из архива к формату базы (заменяем \ на /)
        valid_files = [file for file in all_files if file.replace("\\", "/") in existing_files]

        print(f"Будет извлечено: {len(valid_files)} файлов")

        # Выводим первые 10 файлов для проверки
        print("\nПримеры файлов, которые будут извлечены:")
        for file in valid_files[:10]:
            print(f"  {file}")

        # Спрашиваем подтверждение
        confirm = input("\nПродолжить извлечение? (y/n): ").strip().lower()
        if confirm != "y":
            print("Отмена извлечения.")
            return

        # Создаём папку, если её нет
        os.makedirs(extract_folder, exist_ok=True)

        # Извлекаем только нужные файлы
        for file in valid_files:
            zip_ref.extract(file, extract_folder)
            print(f"Распаковано: {file}")

        print("Извлечение завершено!")

if __name__ == "__main__":
    extract_valid_paintings(ZIP_PATH, EXTRACT_FOLDER)
