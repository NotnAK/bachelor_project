# text_embedding_clip.py
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel

# выбираем устройство
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# более крупная модель CLIP-ViT-L/14
CHECKPOINT = "openai/clip-vit-large-patch14"

# загружаем модель и процессор один раз
model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
processor = CLIPProcessor.from_pretrained(CHECKPOINT)

def generate_text_embedding_clip(text: str) -> np.ndarray:
    """
    Генерирует 768-мерный эмбеддинг для входной строки text
    с помощью CLIP-ViT-L/14.
    """
    model.eval()
    # токенизируем текст
    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(DEVICE)
    # вычисляем эмбеддинг
    with torch.no_grad():
        text_emb = model.get_text_features(**inputs)
        # нормируем вектор (опционально)
        text_emb = text_emb / text_emb.norm(p=2, dim=-1, keepdim=True)
        text_emb_np = text_emb.squeeze(0).cpu().numpy()
    return text_emb_np

if __name__ == "__main__":
    while True:
        query = input("Введите текст для эмбеддинга (exit=выход): ")
        if query.lower() == "exit":
            break
        emb = generate_text_embedding_clip(query)
        print("shape =", emb.shape, "| emb =", emb)
