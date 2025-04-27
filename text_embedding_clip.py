# text_embedding_clip.py
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CHECKPOINT = "openai/clip-vit-base-patch32"

# Загрузим один раз глобально (можно и внутри функции)
model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
processor = CLIPProcessor.from_pretrained(CHECKPOINT)

def generate_text_embedding_clip(text: str) -> np.ndarray:
    model.eval()
    inputs = processor(text=[text], return_tensors="pt", padding=True, truncation=True).to(DEVICE)
    with torch.no_grad():
        text_emb = model.get_text_features(**inputs)
        text_emb = text_emb / text_emb.norm(p=2, dim=-1, keepdim=True)  # опционально, если хотите нормировать
        text_emb_np = text_emb.squeeze(0).cpu().numpy()
    return text_emb_np

if __name__ == "__main__":
    while True:
        query = input("Введите текст для эмбеддинга (exit=выход): ")
        if query.lower() == "exit":
            break
        emb = generate_text_embedding_clip(query)
        print("shape =", emb.shape, "| emb =", emb)
