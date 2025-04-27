import os
import django

# Настроим Django перед импортом моделей
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Укажи путь к папке с картинами
PAINTINGS_FOLDER = r"C:\Users\Антон\Downloads\archive"  # Указываем реальный путь

def clean_paintings(folder):
    """ Удаляет файлы, которых нет в базе данных """
    # Получаем список всех файлов в базе
    existing_files = set(Painting.objects.values_list("filename", flat=True))

    # Проходим по всем файлам в папке и поддиректориях
    for root, _, files in os.walk(folder):
        for file in files:
            file_path = os.path.join(root, file)

            # Если это файл и его нет в базе, удаляем
            if os.path.isfile(file_path) and file not in existing_files:
                print(f"Удаляю {file_path}")
                os.remove(file_path)

if __name__ == "__main__":
    clean_paintings(PAINTINGS_FOLDER)
