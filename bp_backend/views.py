from math import ceil
from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from bp_backend.models import Painting, Artist
import ast

import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection
from bp_backend.models import Painting

from PIL import Image
import os
# Импортируем функцию для загрузки модели
from inference import get_model

# Загружаем модель один раз (глобально)
model = get_model("test_paintings/12", api_key="tapBxwMwkvdW9Of35nNz")

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
            "description": p.description,
            "phash": p.phash,
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
        "description": painting.description,
        "detailed_caption": painting.detailed_caption,  # <-- Добавлено
        "phash": painting.phash,
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
from text_embedding_clip import generate_text_embedding_clip

@api_view(["POST"])
def search_similar_paintings_clip(request):
    """
    Принимает JSON: {"query": "..."}
    Генерируем CLIP‑вектор для текста, ищем в БД картины по близости.
    Возвращает JSON {"results": [...]}.
    """
    data = request.data
    query = data.get("query", "")
    if not query:
        return Response({"error": "No query provided"}, status=400)

    # Генерируем текстовый эмбеддинг
    text_emb = generate_text_embedding_clip(query)  # shape=(512,)
    text_emb_list = text_emb.tolist()

    # В pgvector: ищем 10 ближайших.
    # (!) Если вектор нормированный, то euclidean distance ~ cosine distance.
    #    Можно вместо `<->` использовать `<=>` (оператор cosine).
    #    Но нужно убедиться, что у вас есть оператор <=> в pgvector 0.4+.
    #    Для простоты будем оставлять <-> (L2 distance).
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, filename, embedding <-> %s::vector(512) AS distance
            FROM bp_backend_painting
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s::vector(512)
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

# Импорт модели Paligemma VQA через inference Roboflow
from inference.models.paligemma.paligemma import PaliGemma




@api_view(["POST"])
def search_similar_paintings_clip_vqa(request):
    """
    1. Генерирует CLIP‑эмбеддинг для запроса.
    2. Ищет 10 кандидатов в базе по 512-мерному вектору.
    3. Для каждого кандидата открывает изображение и задаёт вопрос:
       "Does this image contain {query}?" через вызов модели (model.infer).
       Если ответ – "yes", картина включается в результат.
    4. Возвращает JSON с отфильтрованными картинами.
    """
    data = request.data
    query = data.get("query", "").strip()
    if not query:
        return Response({"error": "No query provided."}, status=400)
    try:
        text_emb = generate_text_embedding_clip(query)
    except Exception as e:
        return Response({"error": f"Error generating text embedding: {str(e)}"}, status=500)
    text_emb_list = text_emb.tolist()
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id, filename, embedding <-> %s::vector(512) AS distance
            FROM bp_backend_painting
            WHERE embedding IS NOT NULL
            ORDER BY embedding <-> %s::vector(512)
            LIMIT 10;
        """, [text_emb_list, text_emb_list])
        rows = cursor.fetchall()
    candidate_results = []
    for r in rows:
        candidate_results.append({
            "id": r[0],
            "filename": r[1],
            "distance": r[2]
        })
    final_results = []
    for candidate in candidate_results:
        try:
            painting = get_object_or_404(Painting, id=candidate["id"])
            image_path = os.path.join(settings.MEDIA_ROOT, "extracted_paintings", painting.filename)
            if not os.path.exists(image_path):
                continue
            with Image.open(image_path) as img:
                img = img.convert("RGB")
            # Формируем вопрос для VQA
            vqa_prompt = f"Does this image contain {query}?"
            # Вызываем inference через загруженную модель
            result = model.infer(img, prompt=vqa_prompt)
            answer = str(result[0].response).strip().lower()
        except Exception as e:
            continue
        if answer == "yes":
            final_results.append(candidate)
    return Response({"results": final_results})