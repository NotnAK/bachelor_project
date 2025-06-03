# generate_embeddings_clip.py
import os
import sys
import django

# 1) Инициализируем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

import torch
import numpy as np
from PIL import Image
from bp_backend.models import Painting
from transformers import CLIPProcessor, CLIPModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT = "openai/clip-vit-large-patch14"

# Глобальная «переменная окружения» для префикса
# По умолчанию — ваш старый Naive_Art_Primitivism/
PREFIX = "Naive_Art_Primitivism/"

def generate_embeddings_with_clip():
    """
    Оригинальная функция, НЕ меняется!
    Берёт глобальный PREFIX и фильтрует qs = Painting.objects.filter(filename__startswith=PREFIX)
    """
    print(f"Загружаем модель CLIP: {CHECKPOINT} ...")
    model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(CHECKPOINT)

    qs = Painting.objects.filter(filename__startswith=PREFIX)
    print(f"Найдено {qs.count()} картин для извлечения эмбеддингов CLIP (PREFIX={PREFIX}).")

    count = 0
    for painting in qs:
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print(f"[!] Файл не найден: {image_path}")
            continue
        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"[!] Ошибка при открытии {image_path}: {e}")
            continue

        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            emb = model.get_image_features(**inputs)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            emb_np = emb.squeeze(0).cpu().numpy()

        painting.embedding = emb_np.astype(np.float32).tolist()
        painting.save()
        print(f"Обновлён эмбеддинг для: {painting.filename} | shape={emb_np.shape}")
        count += 1

    print(f"[OK] Всего обновили эмбеддинги для {count} картин.")

def generate_all_embeddings():
    """
    Новая обёртка: пробегает по всем подкаталогам в media/extracted_paintings
    и вызывает generate_embeddings_with_clip для каждой папки.
    """
    global PREFIX

    base_dir = os.path.join("media", "extracted_paintings")
    # Берём только директории!
    prefixes = [name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))]

    for p in sorted(prefixes):
        PREFIX = p + "/"   # обязательно оставляем / на конце
        print("\n" + "="*80)
        print(f"🎯 Обрабатываем категорию: {PREFIX}")
        generate_embeddings_with_clip()


if __name__ == "__main__":
    # 1) чтобы обойтись старым сценарием
    #    просто раскомментируйте:
    # generate_embeddings_with_clip()

    # 2) а чтобы сразу пробежаться по всем папкам:
    generate_all_embeddings()
