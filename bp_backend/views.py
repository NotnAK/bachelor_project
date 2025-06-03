from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
import sys

import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection

from PIL import Image
import numpy as np
from PIL import Image
import ml_collections
import sentencepiece
import functools
import jax
import kagglehub
from django.conf import settings
from math import ceil
from django.db.models import Q

import ast

import logging

logger = logging.getLogger(__name__)
import os
os.environ["KAGGLE_USERNAME"] = "antonkolotusha"
os.environ["KAGGLE_KEY"] = "63cbef5f1f726ac7d1d2c1af0992604c"
# Добавляем репозиторий big_vision в путь поиска модулей
sys.path.append("/home/xkolotusha_122311/bp_backend/big_vision_repo")

# Paligemma Init
sys.path.append("big_vision_repo")
from big_vision.models.proj.paligemma import paligemma
from big_vision.trainers.proj.paligemma import predict_fns


MODEL_PATH = "./models/paligemma-3b-mix-448.f16.npz"
TOKENIZER_PATH = "./models/paligemma_tokenizer.model"
model_config = ml_collections.FrozenConfigDict({
    "llm": {"vocab_size": 257_152},
    "img": {"variant": "So400m/14", "pool_type": "none", "scan": True, "dtype_mm": "float16"}
})
model_pg = paligemma.Model(**model_config)
params_pg = paligemma.load(None, MODEL_PATH, model_config)
tokenizer_pg = sentencepiece.SentencePieceProcessor(TOKENIZER_PATH)
decode_fn_pg = predict_fns.get_all(model_pg)['decode']
decode_pg = functools.partial(decode_fn_pg, devices=jax.devices(), eos_token=tokenizer_pg.eos_id())

def run_example(image_pil, prompt, max_decode_len=128):
    image = image_pil.resize((448, 448)).convert("RGB")
    image_arr = np.array(image).astype(np.float32)
    image_arr = image_arr / 127.5 - 1.0
    image_arr = np.expand_dims(image_arr, axis=0)
    tokens_list = tokenizer_pg.encode(prompt, add_bos=True) + [tokenizer_pg.eos_id()]
    tokens = np.array(tokens_list)[None, :]
    mask_ar = np.zeros_like(tokens)
    mask_input = np.ones_like(tokens)
    batch = {
        "image": image_arr,
        "text": tokens,
        "mask_input": mask_input,
        "mask_ar": mask_ar,
        "_mask": np.array([True])
    }
    output_tokens = decode_pg({"params": params_pg}, batch=batch, max_decode_len=max_decode_len, sampler="greedy")
    tokens_out = np.array(output_tokens)[0].tolist()
    try:
        eos_index = tokens_out.index(tokenizer_pg.eos_id())
        tokens_out = tokens_out[:eos_index]
    except ValueError:
        pass
    return tokenizer_pg.decode(tokens_out)




from django.conf import settings
def parse_genre_field(genre_str):
    if not genre_str:
        return []
    try:
        parsed = ast.literal_eval(genre_str)
        if isinstance(parsed, list):
            return [g.strip() for g in parsed]
        if isinstance(parsed, str):
            return [s.strip() for s in parsed.split(',')]
    except:
        return [s.strip() for s in genre_str.split(',')]
    return []

@api_view(["GET"])
def paintings_list(request):
    """
    Возвращает JSON со списком картин с пагинацией, сортировкой, поиском и фильтрами.
    Параметры запроса: page, sort, order, search, genre, year, artist, page_size
    Формат ответа:
    {
      "results": [...],
      "total_pages": N
    }
    """
    # Параметры запроса
    page = int(request.GET.get("page", 1))
    sort = request.GET.get("sort", "filename")
    order = request.GET.get("order", "asc")
    search = request.GET.get("search", "")
    genre = request.GET.get("genre", "")
    year = request.GET.get("year", "")
    artist_name = request.GET.get("artist", "")

    # Кол-во записей на страницу (по умолчанию 8, но можно менять)
    page_size_str = request.GET.get("page_size", "8")
    try:
        page_size = int(page_size_str)
    except ValueError:
        page_size = 8
    if page_size <= 0:
        page_size = 8

    # Базовый queryset
    queryset = Painting.objects.select_related("artist").all()

    # Фильтрация по поиску (filename, genre, artist.name)
    if search:
        queryset = queryset.filter(
            Q(filename__icontains=search) |
            Q(genre__icontains=search) |
            Q(artist__name__icontains=search)
        )

    # Фильтр по году
    if year:
        queryset = queryset.filter(year=year)

    # Фильтр по художнику
    if artist_name:
        queryset = queryset.filter(artist__name=artist_name)

    # Фильтрация по жанру (сложнее, т.к. может быть несколько)
    # Сначала получим список объектов, потом вручную отфильтруем
    all_paintings = list(queryset)

    if genre:
        filtered_paintings = []
        for p in all_paintings:
            parsed_genres = parse_genre_field(p.genre)
            # Если выбранный жанр входит в список
            if genre in parsed_genres:
                filtered_paintings.append(p)
        all_paintings = filtered_paintings

    # Сортировка (учитываем, что sort может быть "artist_name")
    valid_sort_fields = ["filename", "year", "artist_name", "genre", "id"]
    if sort not in valid_sort_fields:
        sort = "filename"

    # Python-уровневая сортировка (потому что у нас уже список)
    reverse_sort = (order.lower() == "desc")

    if sort == "artist_name":
        all_paintings.sort(key=lambda p: (p.artist.name if p.artist else ""), reverse=reverse_sort)
    elif sort == "genre":
        # Можно сортировать по первому жанру (если их несколько)
        all_paintings.sort(key=lambda p: parse_genre_field(p.genre)[0] if parse_genre_field(p.genre) else "", reverse=reverse_sort)
    else:
        # sort == filename/year/id
        all_paintings.sort(key=lambda p: getattr(p, sort) if getattr(p, sort) is not None else "", reverse=reverse_sort)

    # Пагинация (у нас уже список all_paintings)
    total_count = len(all_paintings)
    total_pages = ceil(total_count / page_size) if total_count > 0 else 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paintings_page = all_paintings[start_index:end_index]

    results = []
    for p in paintings_page:
        results.append({
            "id": p.id,
            "filename": p.filename,
            "genre": p.genre,  # Оставим оригинальную строку
            "name": p.name,
            "width": p.width,
            "height": p.height,
            "genre_count": p.genre_count,
            "year": p.year,
            "artist_id": p.artist.id if p.artist else None,
            "artist_name": p.artist.name if p.artist else None,
            "artist_years": p.artist.years if p.artist else None
        })

    return Response({
        "results": results,
        "total_pages": total_pages
    })

@api_view(["GET"])
def painting_detail(request, pk):
    """
    Возвращает JSON с детальной информацией о картине.
    """
    painting = get_object_or_404(Painting.objects.select_related("artist"), pk=pk)
    data = {
        "id": painting.id,
        "filename": painting.filename,
        "genre": painting.genre,
        "name": painting.name,
        "detailed_caption": painting.detailed_caption,  # <-- Добавлено
        "width": painting.width,
        "height": painting.height,
        "genre_count": painting.genre_count,
        "year": painting.year,
        "artist_id": painting.artist.id if painting.artist else None,
        "artist_name": painting.artist.name if painting.artist else None,
        "artist_years": painting.artist.years if painting.artist else None
    }
    return Response(data)


@api_view(["GET"])
def filter_options(request):
    """
    Возвращает списки уникальных жанров, годов и имен художников для динамических фильтров,
    учитывая уже выбранные параметры (search, genre, year, artist).
    Формат ответа:
    {
      "genres": [...],
      "years": [...],
      "artists": [...]
    }
    """
    search = request.GET.get("search", "")
    genre = request.GET.get("genre", "")
    year = request.GET.get("year", "")
    artist_name = request.GET.get("artist", "")

    queryset = Painting.objects.select_related("artist").all()

    # Фильтр по поиску
    if search:
        queryset = queryset.filter(
            Q(filename__icontains=search) |
            Q(genre__icontains=search) |
            Q(artist__name__icontains=search)
        )

    # Фильтр по году
    if year:
        queryset = queryset.filter(year=year)

    # Фильтр по художнику
    if artist_name:
        queryset = queryset.filter(artist__name=artist_name)

    # Снова, чтобы учесть множественные жанры, придётся python-уровнево:
    all_paintings = list(queryset)
    if genre:
        filtered = []
        for p in all_paintings:
            parsed_genres = parse_genre_field(p.genre)
            if genre in parsed_genres:
                filtered.append(p)
        all_paintings = filtered
    else:
        filtered = all_paintings

    # Теперь собираем множества уникальных значений
    genres_set = set()
    years_set = set()
    artists_set = set()

    for p in all_paintings:
        # Парсим жанры
        parsed_genres = parse_genre_field(p.genre)
        for g in parsed_genres:
            if g:
                genres_set.add(g)

        if p.year:
            years_set.add(p.year)

        if p.artist and p.artist.name:
            artists_set.add(p.artist.name)

    return Response({
        "genres": sorted(genres_set),
        "years": sorted(years_set),
        "artists": sorted(artists_set),
    })
from text_embedding import generate_text_embedding
@api_view(["POST"])  # или GET, на ваше усмотрение
def search_similar_paintings(request):
    """
    Принимает JSON с ключом 'query',
    генерирует вектор текстового эмбеддинга (1024-dim).
    Находит самые похожие картины по cosine / L2 расстоянию.
    Возвращает JSON со списком картин.
    """
    data = request.data
    query_text = data.get("query", "")
    if not query_text:
        return Response({"error": "No query text provided."}, status=400)

    # 1) Генерируем эмбеддинг
    text_emb = generate_text_embedding(query_text)  # numpy array (1024,)

    # 2) Делаем запрос к pgvector
    #    Будем искать топ N (например, 10) самых близких:
    #    SELECT id, (embedding <-> :vector) as distance
    #    FROM bp_backend_painting
    #    ORDER BY distance ASC LIMIT 10;
    #
    #  np array -> list -> передаём как параметр
    text_emb_list = text_emb.tolist()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, filename, embedding <-> %s::vector(1024) AS distance
            FROM bp_backend_painting
            WHERE embedding IS NOT NULL
            ORDER BY embedding <->  %s::vector(1024) 
            LIMIT 10;
        """, [text_emb_list, text_emb_list])
        rows = cursor.fetchall()
        # rows = [(id, filename, distance), ...]

    results = []
    for r in rows:
        painting_id = r[0]
        filename = r[1]
        dist = r[2]
        results.append({
            "id": painting_id,
            "filename": filename,
            "distance": dist
        })

    return Response({"results": results})

# views.py
from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response

from bp_backend.models import Painting
from scripts.text_embedding_clip_768 import generate_text_embedding_clip

@api_view(["POST"])
def search_similar_paintings_clip(request):
    """
    POST /search_similar_paintings_clip/
    {
      "query": "...",
      "caption_weight": 0.3          # вес caption_distance
    }
    """
    data           = request.data
    query          = data.get("query", "").strip()
    caption_weight = float(data.get("caption_weight", 0.0))  # по умолчанию 0

    if not query:
        return Response({"error": "No query provided"}, status=400)

    # 1) CLIP-вектор текста
    text_emb      = generate_text_embedding_clip(query)  # shape=(512,)
    text_emb_list = text_emb.tolist()

    # 2) Топ-K по image_distance
    K = 50
    with connection.cursor() as cursor:
        cursor.execute(f"""
            SELECT id, filename, name,
                   embedding <-> %s::vector(768) AS image_distance
            FROM bp_backend_painting
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s::vector(768)
            LIMIT {K};
        """, [text_emb_list, text_emb_list])
        rows = cursor.fetchall()

    # Словарь id → info
    initial = {
        pid: {"filename": fn, "name": nm, "image_distance": img_dist}
        for pid, fn, nm, img_dist in rows
    }
    ids = list(initial.keys())

    # 3) Берём caption_distance для тех же id
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id,
                   caption_embedding <-> %s::vector(768) AS caption_distance
            FROM bp_backend_painting
            WHERE id = ANY(%s);
        """, [text_emb_list, ids])
        cap_rows = cursor.fetchall()

    # Словарь id → caption_distance
    caption_map = {pid: cap_dist for pid, cap_dist in cap_rows}

    # 4) Считаем combined и сортируем
    results = []
    for pid, info in initial.items():
        img_d = info["image_distance"]
        cap_d = caption_map.get(pid)
        if cap_d is None:
            cap_d = img_d  # fallback на image_distance

        combined = (1 - caption_weight) * img_d + caption_weight * cap_d

        results.append({
            "id": pid,
            "filename": info["filename"],
            "name": info["name"],
            "image_distance": img_d,
            "caption_distance": cap_d,
            "distance": combined,
        })

    # сортируем по combined
    results.sort(key=lambda x: x["distance"])

    return Response({"results": results})


from text_embedding_clip_1024 import generate_text_embedding_clip_1024
@api_view(["POST"])
def search_similar_paintings_clip_1024(request):
    """
    Принимает JSON: {"query": "..."}
    Генерирует 1024-мерный CLIP‑вектор для текста и ищет в БД картины по косинусной (или L2) близости.
    Возвращает JSON {"results": [...]}
    """
    data = request.data
    query = data.get("query", "")
    if not query:
        return Response({"error": "No query provided"}, status=400)

    # Генерируем 1024-мерный текстовый эмбеддинг
    text_emb = generate_text_embedding_clip_1024(query)
    text_emb_list = text_emb.tolist()

    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, filename, embedding <-> %s::vector(1024) AS distance
            FROM bp_backend_painting
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s::vector(1024)
            LIMIT 50;
        """, [text_emb_list, text_emb_list])
        rows = cursor.fetchall()

    results = []
    for row in rows:
        painting_id, filename, dist = row
        results.append({
            "id": painting_id,
            "filename": filename,
            "distance": dist,
        })

    return Response({"results": results})


@api_view(["POST"])
def search_similar_paintings_clip_vqa(request):
    logger.debug("== Начало выполнения search_similar_paintings_clip_vqa ==")
    data = request.data
    query = data.get("query", "").strip()
    if not query:
        logger.warning("Запрос не содержит параметра 'query'")
        return Response({"error": "No query provided."}, status=400)

    logger.info("Получен текстовый запрос: '%s'", query)

    try:
        logger.debug("Генерация CLIP эмбеддинга...")
        from scripts.text_embedding_clip_768 import generate_text_embedding_clip
        text_emb = generate_text_embedding_clip(query)
        logger.debug("Эмбеддинг успешно сгенерирован, размерность: %s", text_emb.shape)
    except Exception as e:
        logger.exception("Ошибка при генерации эмбеддинга: %s", str(e))
        return Response({"error": f"Error generating text embedding: {str(e)}"}, status=500)

    text_emb_list = text_emb.tolist()

    logger.debug("Выполняется SQL-запрос для поиска кандидатов...")
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, filename, embedding <-> %s::vector(768) AS distance
                FROM bp_backend_painting
                WHERE embedding IS NOT NULL
                ORDER BY embedding <-> %s::vector(768)
                LIMIT 50;
            """, [text_emb_list, text_emb_list])
            rows = cursor.fetchall()
        logger.info("Найдено %d кандидатов", len(rows))
    except Exception as e:
        logger.exception("Ошибка при выполнении SQL-запроса: %s", str(e))
        return Response({"error": f"Database error: {str(e)}"}, status=500)

    candidate_results = []
    for r in rows:
        candidate_results.append({
            "id": r[0],
            "filename": r[1],
            "distance": r[2]
        })

    final_results = []
    for candidate in candidate_results:
        painting_id = candidate["id"]
        try:
            logger.info("Обработка кандидата id=%s, filename=%s", painting_id, candidate["filename"])
            painting = get_object_or_404(Painting, id=painting_id)
            image_path = os.path.join(settings.MEDIA_ROOT, "extracted_paintings", painting.filename)
            logger.debug("Путь к изображению: %s", image_path)
            if not os.path.exists(image_path):
                logger.warning("Файл изображения не найден: %s", image_path)
                continue
            with Image.open(image_path) as img:
                img = img.convert("RGB")

            #vqa_prompt = f"does this image contain {query}? Yes or no"
            vqa_prompt = f"does this image contain {query}"
            #vqa_prompt = f"Is there {query} on this image? Yes or no"
            logger.debug("Отправка запроса в Paligemma: '%s'", vqa_prompt)
            answer = run_example(img, f"answer en {vqa_prompt}").strip().lower()
            logger.info("Ответ Paligemma: '%s'", answer)
        except Exception as e:
            logger.exception("Ошибка при обработке кандидата id=%s: %s", painting_id, str(e))
            continue

        if answer.startswith("yes"):
            logger.info("Картина добавлена в результат: id=%s", painting_id)
            final_results.append(candidate)
        else:
            logger.info("Картина отклонена моделью (ответ='%s'): id=%s", answer, painting_id)

    logger.debug("== Завершение search_similar_paintings_clip_vqa ==")
    return Response({"results": final_results})

@api_view(["POST"])
def filter_by_detected_classes(request):
    """
    Принимает JSON:
    {
      "ids": [1, 42, 103, ...],
      "classes": ["dog", "woman", "child"]  # максимум 4 строки
    }
    Возвращает JSON:
    {
      "ids": [ <список id картин, в которых ≥75% пользовательских классов найдены> ]
    }
    """
    data = request.data
    ids = data.get("ids", [])
    classes = data.get("classes", [])

    if not isinstance(ids, list) or not isinstance(classes, list):
        logger.warning("Получены неверные данные: ids или classes не список")
        return Response({"error": "Неверный формат данных"}, status=400)

    # Обрезаем до 4 пользовательских классов, приводим к lowercase
    user_classes = [c.strip().lower() for c in classes if isinstance(c, str)]
    user_classes = user_classes[:4]

    logger.info(f"=== Запущен filter_by_detected_classes: ids={ids}, user_classes={user_classes} ===")

    if len(user_classes) == 0:
        logger.info("Пользователь не задал ни одного класса. Возвращаем пустой список.")
        return Response({"ids": []})

    passed_ids = []

    for pid in ids:
        # Берём объект картины и путь к файлу
        try:
            painting = get_object_or_404(Painting, id=pid)
        except Exception as e:
            logger.warning(f"Painting id={pid} не найден в базе. Пропускаем. Ошибка: {e}")
            continue

        image_path = os.path.join(settings.MEDIA_ROOT, "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            logger.warning(f"Файл изображения для painting id={pid} не найден: {image_path}")
            continue

        logger.info(f"Обрабатываем картину: id={pid}, filename='{painting.filename}'")

        # Формируем prompt
        prompt = "detect " + "; ".join(user_classes)
        logger.info(f"Формируем prompt для Paligemma: '{prompt}'")

        # Запускаем Paligemma
        try:
            with Image.open(image_path) as img_obj:
                img = img_obj.convert("RGB")
                output_str = run_example(img, prompt).strip()
        except Exception as e:
            logger.error(f"Ошибка при запуске Paligemma для id={pid}: {e}")
            continue

        logger.info(f"Paligemma вернул для id={pid}: \"{output_str}\"")

        # Парсим выход Paligemma: split по ";" и берём последние слова как «классы»
        detected_classes = set()
        for piece in output_str.split(";"):
            cls = piece.strip().lower()
            if not cls:
                continue
            parts = cls.split()
            # берём последний токен (это и будет «класс»)
            last_word = parts[-1]
            detected_classes.add(last_word)

        logger.info(f"Найденные уникальные классы в картине id={pid}: {detected_classes}")

        # Считаем пересечение
        match_count = len(set(user_classes) & detected_classes)
        logger.info(
            f"Количество совпадений с user_classes для id={pid}: {match_count} "
            f"из {len(user_classes)} ({match_count/len(user_classes)*100:.1f}% )"
        )

        if match_count / len(user_classes) >= 0.75:
            logger.info(f"--> Картину id={pid} ВКЛЮЧАЕМ в результат (match_count={match_count}).")
            passed_ids.append(pid)
        else:
            logger.info(f"--> Картину id={pid} ОТКЛОНЯЕМ (match_count={match_count}).")

    logger.info(f"=== Результат filter_by_detected_classes: passed_ids={passed_ids} ===")
    return Response({"ids": passed_ids})
