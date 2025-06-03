import os, sys, django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

import torch
import numpy as np
from bp_backend.models import Painting
from transformers import CLIPTokenizer, CLIPModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
CHECKPOINT = "openai/clip-vit-large-patch14"  # Better model, 768-dimensional embeddings

def generate_caption_embeddings():
    print(f"Loading CLIP text model: {CHECKPOINT}")
    model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
    tokenizer = CLIPTokenizer.from_pretrained(CHECKPOINT)

    qs = Painting.objects.exclude(detailed_caption__isnull=True).exclude(detailed_caption__exact="")
    print(f"Found {qs.count()} records with AI-generated captions.")
    for painting in qs:
        text = painting.detailed_caption
        inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True).to(DEVICE)
        with torch.no_grad():
            emb = model.get_text_features(**inputs)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            emb_np = emb.squeeze(0).cpu().numpy()
        painting.caption_embedding = emb_np.astype(np.float32).tolist()
        painting.save(update_fields=["caption_embedding"])
        print(f"Saved embedding for id={painting.id}")

if __name__ == "__main__":
    generate_caption_embeddings()
