# generate_embeddings_clip.py
import os
import sys
import django

# 1) Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

import torch
import numpy as np
from PIL import Image
from bp_backend.models import Painting
from transformers import CLIPProcessor, CLIPModel

DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

CHECKPOINT = "openai/clip-vit-large-patch14"

def generate_embeddings_with_clip():
    print(f"Loading CLIP model: {CHECKPOINT} ...")
    model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(CHECKPOINT)

    # Filter paintings, e.g. all or only Baroque, as needed
    # qs = Painting.objects.all()
    qs = Painting.objects.filter(filename__startswith="Naive_Art_Primitivism/")
    print(f"Found {qs.count()} paintings for CLIP embedding extraction.")

    count = 0
    for painting in qs:
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print(f"[!] File not found: {image_path}")
            continue

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"[!] Error opening {image_path}: {e}")
            continue

        # Prepare image for CLIP
        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            # Pass through the image encoder
            emb = model.get_image_features(**inputs)
            # Normalize (optional), or store as is
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            emb_np = emb.squeeze(0).cpu().numpy()

        # Save to model
        painting.embedding = emb_np.astype(np.float32).tolist()
        painting.save()
        print(f"Updated embedding for: {painting.filename} | shape={emb_np.shape}")
        count += 1

    print(f"[OK] Total embeddings updated for {count} paintings.")

if __name__ == "__main__":
    generate_embeddings_with_clip()
