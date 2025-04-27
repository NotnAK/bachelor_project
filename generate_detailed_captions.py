# generate_detailed_captions.py
import os
import django
from PIL import Image
from inference import get_model  # Импорт Roboflow‑функции для загрузки модели

# Инициализируем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Ваш API-ключ Roboflow
API_KEY = "tapBxwMwkvdW9Of35nNz"

# Загружаем модель Florence‑2 через Roboflow (не вызываем eval, так как у объекта его нет)
model = get_model("florence-2-base", api_key=API_KEY)


def generate_detailed_captions_for_paintings():
    # Здесь можно задать фильтр для выбора картин (например, по папке или другим критериям)
    qs = Painting.objects.filter(filename__startswith="Realism/")  # Замените на нужное условие
    print(f"Найдено {qs.count()} картин для генерации подробных описаний.")

    count = 0
    for painting in qs:
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print(f"Файл не найден: {image_path}")
            continue

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"Ошибка при открытии {image_path}: {e}")
            continue

        try:
            # Генерируем подробное описание, передавая нужный промпт
            result = model.infer(img, prompt="<MORE_DETAILED_CAPTION>")
            # Ожидается, что результат возвращается как список объектов, где в первом элементе находится response
            caption = result[0].response.get("<MORE_DETAILED_CAPTION>")
            if caption is None:
                # Если структура результата иная – можно попробовать вывести весь response
                caption = result[0].response
        except Exception as e:
            print(f"Ошибка при генерации описания для {painting.filename}: {e}")
            continue

        # Сохраняем сгенерированное описание в новое поле detailed_caption
        painting.detailed_caption = caption
        painting.save()
        print(f"Обновлён подробный текст для: {painting.filename}")
        count += 1

    print(f"Всего обновлены подробные описания для {count} картин.")


if __name__ == "__main__":
    generate_detailed_captions_for_paintings()
