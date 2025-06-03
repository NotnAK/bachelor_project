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
model_id = "microsoft/Florence-2-large"
model = AutoModelForCausalLM.from_pretrained(
    model_id, trust_remote_code=True, torch_dtype='auto'
).eval().cuda()
processor = AutoProcessor.from_pretrained(
    model_id, trust_remote_code=True
)

# Промпт для генерации описаний
task_prompt = "<MORE_DETAILED_CAPTION>"

# Глобальная «переменная окружения» для префикса папки
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
    Оригинальная функция, НЕ менять по части логики:
    берёт глобальный PREFIX и фильтрует:
      Painting.objects.filter(filename__startswith=PREFIX)
    Но теперь выводит порядковый номер и помечает,
    есть ли уже caption.
    """
    qs = Painting.objects.filter(filename__startswith=PREFIX)
    total = qs.count()
    print(f"🔍 Найдено {total} картин (PREFIX={PREFIX}).\n")

    updated = 0
    for idx, painting in enumerate(qs, start=1):
        # Выводим номер и имя
        print(f"{idx}. {painting.filename} —", end=" ")

        # Если описание уже есть — пропускаем генерацию
        if painting.detailed_caption:
            print("пропущено (описание уже есть)")
            continue

        # Иначе — генерируем
        image_path = os.path.join("media", "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            print(f"❌ файл не найден")
            continue

        try:
            with Image.open(image_path) as img:
                img = img.convert("RGB")
        except Exception as e:
            print(f"❌ ошибка при открытии: {e}")
            continue

        try:
            caption = run_caption(img, task_prompt)
        except Exception as e:
            print(f"❌ ошибка генерации: {e}")
            continue

        # Сохраняем и отмечаем
        painting.detailed_caption = caption
        painting.save()
        updated += 1
        print("✅ обновлено")

    print(f"\n🎉 Всего обновлено описаний: {updated} из {total}.")


def generate_all_captions():
    """
    Новая обёртка: пробегает по всем поддиректориям
    в media/extracted_paintings и для каждой меняет PREFIX,
    а затем вызывает generate_detailed_captions_for_paintings().
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
        print(f"🎯 Обрабатываем категорию: {PREFIX}")
        generate_detailed_captions_for_paintings()


if __name__ == "__main__":
    # Для одного каталога:
    # generate_detailed_captions_for_paintings()

    # Для всех сразу:
    generate_all_captions()
