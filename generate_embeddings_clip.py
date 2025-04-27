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

CHECKPOINT = "openai/clip-vit-base-patch32"

def generate_embeddings_with_clip():
    print(f"Загружаем модель CLIP: {CHECKPOINT} ...")
    model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(CHECKPOINT)

    # Фильтруем картины, например все или только Baroque, как вам нужно
    #qs = Painting.objects.all()
    qs = Painting.objects.filter(filename__startswith="Realism/")
    print(f"Найдено {qs.count()} картин для извлечения эмбеддингов CLIP.")

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

        # Преобразуем изображение для CLIP
        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            # Прогоняем через image_encoder
            emb = model.get_image_features(**inputs)
            # Нормируем (опционально), или можно хранить «как есть»
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            emb_np = emb.squeeze(0).cpu().numpy()

        # Сохраняем в модель
        painting.embedding = emb_np.astype(np.float32).tolist()
        painting.save()
        print(f"Обновлён эмбеддинг для: {painting.filename} | shape={emb_np.shape}")
        count += 1

    print(f"[OK] Всего обновили эмбеддинги для {count} картин.")

if __name__ == "__main__":
    generate_embeddings_with_clip()
