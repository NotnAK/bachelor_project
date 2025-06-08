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

# Global “environment variable” for prefix
# Default is your old Naive_Art_Primitivism/
PREFIX = "Naive_Art_Primitivism/"

def generate_embeddings_with_clip():
    """
    Original function – do NOT change!
    Uses global PREFIX and filters qs = Painting.objects.filter(filename__startswith=PREFIX)
    """
    print(f"Loading CLIP model: {CHECKPOINT} ...")
    model = CLIPModel.from_pretrained(CHECKPOINT).to(DEVICE)
    processor = CLIPProcessor.from_pretrained(CHECKPOINT)

    qs = Painting.objects.filter(filename__startswith=PREFIX)
    print(f"Found {qs.count()} paintings for CLIP embedding extraction (PREFIX={PREFIX}).")

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

        inputs = processor(images=img, return_tensors="pt").to(DEVICE)
        with torch.no_grad():
            emb = model.get_image_features(**inputs)
            emb = emb / emb.norm(p=2, dim=-1, keepdim=True)
            emb_np = emb.squeeze(0).cpu().numpy()

        painting.embedding = emb_np.astype(np.float32).tolist()
        painting.save()
        print(f"Updated embedding for: {painting.filename} | shape={emb_np.shape}")
        count += 1

    print(f"[OK] Total embeddings updated for {count} paintings.")

def generate_all_embeddings():
    """
    New wrapper: iterates through all subdirectories in media/extracted_paintings
    and calls generate_embeddings_with_clip for each folder.
    """
    global PREFIX

    base_dir = os.path.join("media", "extracted_paintings")
    # Only take directories!
    prefixes = [name for name in os.listdir(base_dir) if os.path.isdir(os.path.join(base_dir, name))]

    for p in sorted(prefixes):
        PREFIX = p + "/"   # make sure to keep the trailing slash
        print("\n" + "="*80)
        print(f"🎯 Processing category: {PREFIX}")
        generate_embeddings_with_clip()

if __name__ == "__main__":
    # 1) To use the old scenario, just uncomment:
    # generate_embeddings_with_clip()

    # 2) To run for all folders at once:
    generate_all_embeddings()
