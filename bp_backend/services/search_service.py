# bp_backend/services/search_service.py

import os
import logging

from django.db import connection
from django.shortcuts import get_object_or_404
from django.conf import settings

from PIL import Image

from bp_backend.models import Painting
from .paligemma_service import run_example

logger = logging.getLogger(__name__)


def search_similar_paintings_clip_service(query: str, caption_weight: float) -> list[dict]:
    """
    Accepts a query string and caption_weight value.
    Returns a list of dicts where each dict = {"id", "filename", "name", "image_distance", "caption_distance", "distance"}.
    The code inside these functions is taken from your original view and remains unchanged,
    except that we've lifted it into a service.
    """
    # 1) CLIP text vector (since you generate it “on the fly”)
    from scripts.text_embedding_clip_768 import generate_text_embedding_clip
    text_emb = generate_text_embedding_clip(query)  # numpy array (768,)
    text_emb_list = text_emb.tolist()

    # 2) Top-K by image_distance
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

    # Build a dict id → info
    initial = {
        pid: {"filename": fn, "name": nm, "image_distance": img_dist}
        for pid, fn, nm, img_dist in rows
    }
    ids = list(initial.keys())

    # 3) Get caption_distance for the same ids
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT id,
                   caption_embedding <-> %s::vector(768) AS caption_distance
            FROM bp_backend_painting
            WHERE id = ANY(%s);
        """, [text_emb_list, ids])
        cap_rows = cursor.fetchall()

    # Dict id → caption_distance
    caption_map = {pid: cap_dist for pid, cap_dist in cap_rows}

    # 4) Compute combined and sort
    results = []
    for pid, info in initial.items():
        img_d = info["image_distance"]
        cap_d = caption_map.get(pid, img_d)  # fallback to image_distance

        combined = (1 - caption_weight) * img_d + caption_weight * cap_d

        results.append({
            "id": pid,
            "filename": info["filename"],
            "name": info["name"],
            "image_distance": img_d,
            "caption_distance": cap_d,
            "distance": combined,
        })

    # Sort by combined
    results.sort(key=lambda x: x["distance"])
    return results


def search_similar_paintings_clip_vqa_service(query: str) -> list[dict]:
    """
    Accepts a query string, returns a list of dicts for candidates filtered by Paligemma VQA (Yes/No).
    Each dict = {"id", "filename", "distance"}.
    The code below is your original code, only moved here.
    """
    logger.debug("== Starting search_similar_paintings_clip_vqa_service ==")
    # 1) Generate CLIP embedding
    try:
        from scripts.text_embedding_clip_768 import generate_text_embedding_clip
        text_emb = generate_text_embedding_clip(query)
        logger.debug("Embedding successfully generated, shape: %s", text_emb.shape)
    except Exception as e:
        logger.exception("Error generating embedding: %s", str(e))
        raise

    text_emb_list = text_emb.tolist()

    # 2) SQL query for candidates
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
        logger.info("Found %d candidates", len(rows))
    except Exception as e:
        logger.exception("Error executing SQL query: %s", str(e))
        raise

    candidate_results = [
        {"id": pid, "filename": fn, "distance": dist}
        for pid, fn, dist in rows
    ]

    final_results = []
    for candidate in candidate_results:
        painting_id = candidate["id"]
        try:
            painting = get_object_or_404(Painting, id=painting_id)
            image_path = os.path.join(settings.MEDIA_ROOT, "extracted_paintings", painting.filename)
            logger.debug("Image path: %s", image_path)
            if not os.path.exists(image_path):
                logger.warning("Image file not found: %s", image_path)
                continue

            with Image.open(image_path).convert("RGB") as img:
                vqa_prompt = f"does this image contain {query}"
                logger.debug("Sending request to Paligemma: '%s'", vqa_prompt)
                answer = run_example(img, f"answer en {vqa_prompt}").strip().lower()
                logger.info("Paligemma answer: '%s'", answer)
        except Exception as e:
            logger.exception("Error processing candidate id=%s: %s", painting_id, str(e))
            continue

        if answer.startswith("yes"):
            logger.info("Painting added to result: id=%s", painting_id)
            final_results.append({
                "id": candidate["id"],
                "filename": candidate["filename"],
                "distance": candidate["distance"]
            })
        else:
            logger.info("Painting rejected by model (answer='%s'): id=%s", answer, painting_id)

    logger.debug("== Ending search_similar_paintings_clip_vqa_service ==")
    return final_results


def filter_by_detected_classes_service(ids: list[int], classes: list[str]) -> list[int]:
    """
    Accepts a list of ids and a list of class strings (max 4 items),
    returns a list of those ids for which Paligemma finds ≥75% of the classes.
    The code inside is completely your original code, just moved here.
    """
    if not isinstance(ids, list) or not isinstance(classes, list):
        logger.warning("Received invalid data: ids or classes not a list")
        raise ValueError("ids and classes must be lists")

    user_classes = [c.strip().lower() for c in classes if isinstance(c, str)]
    user_classes = user_classes[:4]
    logger.info(f"=== Running filter_by_detected_classes_service: ids={ids}, user_classes={user_classes} ===")

    if not user_classes:
        logger.info("No user classes provided. Returning empty list.")
        return []

    passed_ids = []
    for pid in ids:
        try:
            painting = get_object_or_404(Painting, id=pid)
        except Exception as e:
            logger.warning(f"Painting id={pid} not found in DB. Skipping. Error: {e}")
            continue

        image_path = os.path.join(settings.MEDIA_ROOT, "extracted_paintings", painting.filename)
        if not os.path.exists(image_path):
            logger.warning(f"Image file for painting id={pid} not found: {image_path}")
            continue

        logger.info(f"Processing painting: id={pid}, filename='{painting.filename}'")

        prompt = "detect " + "; ".join(user_classes)
        logger.info(f"Building prompt for Paligemma: '{prompt}'")

        try:
            with Image.open(image_path).convert("RGB") as img:
                output_str = run_example(img, prompt).strip()
        except Exception as e:
            logger.error(f"Error running Paligemma for id={pid}: {e}")
            continue

        logger.info(f"Paligemma returned for id={pid}: \"{output_str}\"")

        detected_classes = set()
        for piece in output_str.split(";"):
            cls = piece.strip().lower()
            if not cls:
                continue
            last_word = cls.split()[-1]
            detected_classes.add(last_word)

        logger.info(f"Unique detected classes in painting id={pid}: {detected_classes}")

        match_count = len(set(user_classes) & detected_classes)
        logger.info(
            f"Number of matches with user_classes for id={pid}: {match_count} "
            f"out of {len(user_classes)} ({match_count/len(user_classes)*100:.1f}% )"
        )

        if match_count / len(user_classes) >= 0.75:
            logger.info(f"--> Including painting id={pid} in result (match_count={match_count}).")
            passed_ids.append(pid)
        else:
            logger.info(f"--> Rejecting painting id={pid} (match_count={match_count}).")

    logger.info(f"=== Result of filter_by_detected_classes_service: passed_ids={passed_ids} ===")
    return passed_ids
