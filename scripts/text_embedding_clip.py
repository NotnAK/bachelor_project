# text_embedding_clip.py
import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()
import torch
import numpy as np
from transformers import CLIPProcessor, CLIPModel

# Choose device
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# Larger CLIP-ViT-L/14 model
CHECKPOINT = "openai/clip-vit-large-patch14"

# Load model and processor once
model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
processor = CLIPProcessor.from_pretrained(CHECKPOINT)

def generate_text_embedding_clip(text: str) -> np.ndarray:
    """
    Generates a 768-dimensional embedding for the input text using CLIP-ViT-L/14.
    """
    model.eval()
    # Tokenize text
    inputs = processor(
        text=[text],
        return_tensors="pt",
        padding=True,
        truncation=True
    ).to(DEVICE)
    # Compute embedding
    with torch.no_grad():
        text_emb = model.get_text_features(**inputs)
        # Normalize the vector (optional)
        text_emb = text_emb / text_emb.norm(p=2, dim=-1, keepdim=True)
        text_emb_np = text_emb.squeeze(0).cpu().numpy()
    return text_emb_np

if __name__ == "__main__":
    while True:
        query = input("Enter text for embedding (exit=quit): ")
        if query.lower() == "exit":
            break
        emb = generate_text_embedding_clip(query)
        print("shape =", emb.shape, "| emb =", emb)
