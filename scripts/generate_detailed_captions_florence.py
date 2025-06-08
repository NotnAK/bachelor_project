# generate_detailed_captions.py
import os
import django
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

# Initialize Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Load model and processor
model_id = "microsoft/Florence-2-large"
model = AutoModelForCausalLM.from_pretrained(
    model_id, trust_remote_code=True, torch_dtype='auto'
).eval().cuda()
processor = AutoProcessor.from_pretrained(
    model_id, trust_remote_code=True
)

# Prompt to generate captions
task_prompt = "<MORE_DETAILED_CAPTION>"

# Global “environment variable” for folder prefix
PREFIX = "Realism/"

def run_caption(image: Image.Image, task_prompt: str) -> str:
    inputs = processor(
        text=task_prompt,
        images=image,
        return_tensors="pt"
    ).to("cuda", torch.float16)

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )

    generated_text = processor.batch_decode(
        generated_ids,
        skip_special_tokens=False
    )[0]
    parsed = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(image.width, image.height)
    )
    if isinstance(parsed, dict):
        return parsed.get(task_prompt, "")
    return parsed

def generate_detailed_captions_for_paintings():
    """
    Original function – do NOT change logic:
    uses global PREFIX and filters:
      Painting.objects.filter(filename__startswith=PREFIX)
    Now prints index and marks if a caption already exists.
    """
    qs = Painting.objects.filter(filename__startswith=PREFIX)
    total = qs.count()
    print(f"🔍 Found {total} paintings (PREFIX={PREFIX}).\n")

    updated = 0
    for idx, painting in enumerate(qs, start=1):
        # Print index and filename
        print(f"{idx}. {painting.filename} —", end=" ")

        # If a caption already exists, skip generation
        if painting.detailed_caption:
            print("skipped (caption already exists)")
            continue

        # Otherwise – generate
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print("❌ file not found")
            continue

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"❌ error opening: {e}")
            continue

        try:
            caption = run_caption(img, task_prompt)
        except Exception as e:
            print(f"❌ generation error: {e}")
            continue

        # Save and mark
        painting.detailed_caption = caption
        painting.save()
        updated += 1
        print("✅ updated")

    print(f"\n🎉 Total captions updated: {updated} out of {total}.")

def generate_all_captions():
    """
    New wrapper: iterates through all subdirectories
    in media/extracted_paintings and for each changes PREFIX,
    then calls generate_detailed_captions_for_paintings().
    """
    global PREFIX

    base_dir = os.path.join("media", "extracted_paintings")
    prefixes = [
        name for name in os.listdir(base_dir)
        if os.path.isdir(os.path.join(base_dir, name))
    ]

    for p in sorted(prefixes):
        PREFIX = f"{p}/"
        print("\n" + "="*80)
        print(f"🎯 Processing category: {PREFIX}")
        generate_detailed_captions_for_paintings()

if __name__ == "__main__":
    # For a single category:
    # generate_detailed_captions_for_paintings()

    # Or to do all at once:
    generate_all_captions()
