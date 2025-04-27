# text_embedding_clip_1024.py
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT = "laion/CLIP-ViT-H-14-laion2B-s32B-b79K"  # Модель, возвращающая 1024-мерные эмбеддинги

# Загружаем модель и процессор
model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
processor = CLIPProcessor.from_pretrained(CHECKPOINT)

def generate_text_embedding_clip_1024(text: str) -> np.ndarray:
    """
    Генерирует 1024-мерный текстовый эмбеддинг для переданного текста.
    """
    model.eval()
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(DEVICE)
    with torch.no_grad():
        text_features = model.get_text_features(**inputs)
        # Нормализация вектора (L2-норма)
        text_features = text_features / text_features.norm(p=2, dim=-1, keepdim=True)
    return text_features.squeeze(0).cpu().numpy()

if __name__ == "__main__":
    while True:
        query = input("Введите текст для эмбеддинга (exit=выход): ")
        if query.lower() == "exit":
            break
        emb = generate_text_embedding_clip_1024(query)
        print("shape =", emb.shape, "| emb =", emb)
