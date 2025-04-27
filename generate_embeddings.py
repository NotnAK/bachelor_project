import os
import django

# 1) Настройка Django
# Устанавливаем переменную окружения, указывающую, где находятся настройки Django-проекта
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
# Запускаем Django (инициализируем ORM и подключение к базе)
django.setup()

# 2) Импорт необходимых библиотек
import torch  # Библиотека для работы с тензорами и нейросетями
import numpy as np  # Для работы с массивами
from PIL import Image  # Библиотека для загрузки и обработки изображений
from bp_backend.models import Painting  # Импорт модели картины из базы данных
from transformers import AutoModelForCausalLM, AutoProcessor  # Модель Florence-2 и её обработчик

# 3) Параметры модели Florence-2
CHECKPOINT = "microsoft/Florence-2-base-ft"  # Название предобученной модели
REVISION = "refs/pr/6"  # Используемая ревизия модели
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # Используем GPU, если доступно

def generate_embeddings_for_baroque():
    """
    Генерирует эмбеддинги изображений с помощью модели Florence-2 и сохраняет их в базу данных.
    """

    print(f"Загружаем модель Florence‑2 ({CHECKPOINT}), revision={REVISION}...")
    # Загружаем предобученную модель Florence-2
    model = AutoModelForCausalLM.from_pretrained(
        CHECKPOINT,
        trust_remote_code=True,
        revision=REVISION
    ).to(DEVICE)

    # Загружаем процессор, который обрабатывает изображения перед подачей в модель
    processor = AutoProcessor.from_pretrained(
        CHECKPOINT,
        trust_remote_code=True,
        revision=REVISION
    )

    # 4) Фильтруем картины для обработки
    # Выбираем только картины, название файла которых начинается с "Realism/"
    qs = Painting.objects.filter(filename__startswith="Realism/")
    print(f"Найдено {qs.count()} картин из папки Realism.")

    count = 0  # Счётчик обработанных картин
    for painting in qs:
        # Формируем путь к файлу изображения
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):  # Проверяем, существует ли файл
            print(f"Файл не найден: {image_path}")
            continue  # Пропускаем обработку, если файла нет

        try:
            # Открываем изображение и конвертируем его в RGB-формат (чтобы избежать несовместимости)
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"Ошибка при открытии {image_path}: {e}")
            continue  # Пропускаем файл, если возникла ошибка при открытии

        try:
            # 5) Подготовка входных данных для модели Florence-2
            # Используем текстовый промпт "<DETAILED_CAPTION>" для обработки изображения
            inputs = processor(text="<DETAILED_CAPTION>", images=img, return_tensors="pt").to(DEVICE)
            if "pixel_values" not in inputs:
                print(f"Отсутствуют pixel_values для {painting.filename}")
                continue

            with torch.no_grad():  # Отключаем градиенты, так как мы не обучаем модель
                # Получаем визуальные признаки изображения через vision-tower модели Florence-2
                vision_tokens = model.vision_tower.forward_features_unpool(inputs["pixel_values"])
                # Усредняем векторы признаков по всем токенам (spatial average pooling)
                pooled = vision_tokens.mean(dim=1)

                # 6) Проверяем, есть ли в модели встроенная проекция (обычно используется Florence2VisionModelWithProjection)
                if hasattr(model.vision_tower, "image_projection") and hasattr(model.vision_tower, "image_proj_norm"):
                    # Применяем проекцию и нормализацию
                    projected = pooled @ model.vision_tower.image_projection
                    projected = model.vision_tower.image_proj_norm(projected)
                else:
                    projected = pooled  # Если проекции нет, используем просто усреднённый вектор

                # L2-нормализация эмбеддинга (приведение к единичной длине)
                norm = torch.norm(projected, p=2, dim=-1, keepdim=True)
                emb = projected / norm
                # Переводим вектор с GPU на CPU и преобразуем в формат numpy
                final_emb = emb.squeeze(0).cpu().numpy()

        except Exception as e:
            print(f"Ошибка при генерации эмбеддинга для {painting.filename}: {e}")
            continue  # Пропускаем изображение, если возникает ошибка

        # 7) Сохраняем эмбеддинг в базу данных
        painting.embedding = final_emb.astype(np.float32).tolist()  # Преобразуем numpy-массив в список для хранения
        painting.save()
        print(f"Обновлён эмбеддинг для {painting.filename} (размер: {final_emb.shape})")
        count += 1  # Увеличиваем счётчик обработанных изображений

    print(f"Всего обновлено эмбеддингов для {count} картин.")

# 8) Запуск скрипта
if __name__ == "__main__":
    generate_embeddings_for_baroque()
