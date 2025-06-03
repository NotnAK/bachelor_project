from django.db.models import Q
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.shortcuts import get_object_or_404

import numpy as np
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.db import connection

from django.db import connection
from rest_framework.decorators import api_view
from rest_framework.response import Response

from PIL import Image
import numpy as np
from PIL import Image
import ml_collections
import sentencepiece
import jax
import kagglehub
from django.conf import settings
from django.db.models import Q
import ast
from .services.painting_service import (
    get_paintings_list,
    get_painting_detail,
    get_filter_options
)

from .services.search_service import (
    search_similar_paintings_clip_service,
    search_similar_paintings_clip_vqa_service,
    filter_by_detected_classes_service
)
import logging

logger = logging.getLogger(__name__)

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
    Calls the get_paintings_list service, passes all necessary GET parameters,
    and returns JSON {"results": [...], "total_pages": N}.
    """
    params = {
        "page": request.GET.get("page", 1),
        "sort": request.GET.get("sort", "filename"),
        "order": request.GET.get("order", "asc"),
        "search": request.GET.get("search", ""),
        "genre": request.GET.get("genre", ""),
        "year": request.GET.get("year", ""),
        "artist": request.GET.get("artist", ""),
        "page_size": request.GET.get("page_size", "8"),
    }

    results, total_pages = get_paintings_list(params)
    return Response({
        "results": results,
        "total_pages": total_pages
    })


@api_view(["GET"])
def painting_detail(request, pk):
    """
    Calls the get_painting_detail service and returns the data as a dictionary.
    """
    data = get_painting_detail(pk)
    return Response(data)


@api_view(["GET"])
def filter_options(request):
    """
    Calls the get_filter_options service and returns JSON {"genres": [...], "years": [...], "artists": [...]}.
    """
    params = {
        "search": request.GET.get("search", ""),
        "genre": request.GET.get("genre", ""),
        "year": request.GET.get("year", ""),
        "artist": request.GET.get("artist", ""),
    }
    data = get_filter_options(params)
    return Response(data)


@api_view(["POST"])
def search_similar_paintings_clip(request):
    """
    POST /search_similar_paintings_clip/  {"query": "...", "caption_weight": 0.3}
    Calls the search_similar_paintings_clip_service and returns its result as JSON.
    """
    data = request.data
    query = data.get("query", "").strip()
    caption_weight = float(data.get("caption_weight", 0.0))

    if not query:
        return Response({"error": "No query provided"}, status=400)

    try:
        results = search_similar_paintings_clip_service(query, caption_weight)
    except Exception as e:
        logger.exception("Error in search_similar_paintings_clip_service: %s", e)
        return Response({"error": f"Internal error: {str(e)}"}, status=500)

    return Response({"results": results})


@api_view(["POST"])
def search_similar_paintings_clip_vqa(request):
    """
    POST /search_similar_paintings_clip_vqa/  {"query": "..."}
    Calls the search_similar_paintings_clip_vqa_service and returns its result as JSON.
    """
    data = request.data
    query = data.get("query", "").strip()

    if not query:
        return Response({"error": "No query provided."}, status=400)

    try:
        results = search_similar_paintings_clip_vqa_service(query)
    except Exception as e:
        logger.exception("Error in search_similar_paintings_clip_vqa_service: %s", e)
        return Response({"error": f"Internal error: {str(e)}"}, status=500)

    return Response({"results": results})


@api_view(["POST"])
def filter_by_detected_classes(request):
    """
    POST /filter_by_detected_classes/  {"ids": [...], "classes": ["dog", "woman", "child"]}
    Calls the filter_by_detected_classes_service and returns its result: {"ids": [...]}
    """
    data = request.data
    ids = data.get("ids", [])
    classes = data.get("classes", [])

    try:
        passed_ids = filter_by_detected_classes_service(ids, classes)
    except ValueError as e:
        logger.warning("Invalid data format in filter_by_detected_classes: %s", e)
        return Response({"error": "Invalid data format"}, status=400)
    except Exception as e:
        logger.exception("Error in filter_by_detected_classes_service: %s", e)
        return Response({"error": f"Internal error: {str(e)}"}, status=500)

    return Response({"ids": passed_ids})
