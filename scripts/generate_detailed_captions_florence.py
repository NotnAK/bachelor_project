# generate_detailed_captions.py
import os
import django
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM
import torch

# Инициализируем Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bp_backend.settings")
django.setup()

from bp_backend.models import Painting

# Загружаем модель и препроцессор
model_id = "microsoft/Florence-2-large-ft"
# or you can use microsoft/Florence-2-large
model = AutoModelForCausalLM.from_pretrained(model_id, trust_remote_code=True, torch_dtype='auto').eval().cuda()
processor = AutoProcessor.from_pretrained(model_id, trust_remote_code=True)

# Промпт для генерации описаний
task_prompt = "<MORE_DETAILED_CAPTION>"


def run_caption(image: Image.Image, task_prompt: str) -> str:
    prompt = task_prompt
    inputs = processor(text=prompt, images=image, return_tensors="pt").to("cuda", torch.float16)

    with torch.no_grad():
        generated_ids = model.generate(
            input_ids=inputs["input_ids"],
            pixel_values=inputs["pixel_values"],
            max_new_tokens=1024,
            early_stopping=False,
            do_sample=False,
            num_beams=3,
        )

    generated_text = processor.batch_decode(generated_ids, skip_special_tokens=False)[0]
    parsed_answer = processor.post_process_generation(
        generated_text,
        task=task_prompt,
        image_size=(image.width, image.height)
    )
    if isinstance(parsed_answer, dict):
        return parsed_answer.get("<MORE_DETAILED_CAPTION>", "")
    return parsed_answer


def generate_detailed_captions_for_paintings():
    qs = Painting.objects.filter(filename__startswith="Northern_Renaissance/")
    print(f"Найдено {qs.count()} картин для генерации подробных описаний.")

    count = 0
    for painting in qs:
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print(f"❌ Файл не найден: {image_path}")
            continue

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"❌ Ошибка при открытии {image_path}: {e}")
            continue

        try:
            caption = run_caption(img, task_prompt)
        except Exception as e:
            print(f"❌ Ошибка генерации описания для {painting.filename}: {e}")
            continue
        if painting.detailed_caption:
            print("пропущено (описание уже есть)")
            print("Старое описание: " + painting.detailed_caption)
            print("\n Новое описание:" + caption)
            continue

        painting.detailed_caption = caption
        painting.save()
        print(f"✅ Обновлён подробный текст для: {painting.filename}")
        count += 1

    print(f"🎉 Всего обновлены подробные описания для {count} картин.")


if __name__ == "__main__":
    generate_detailed_captions_for_paintings()
