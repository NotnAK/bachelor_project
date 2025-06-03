# bp_backend/services/painting_service.py

from math import ceil
from django.db.models import Q
from django.shortcuts import get_object_or_404

from bp_backend.models import Painting


def parse_genre_field(genre_str: str) -> list[str]:
    """
    Copy of your function from views.py for parsing the genre field.
    """
    import ast
    if not genre_str:
        return []
    try:
        parsed = ast.literal_eval(genre_str)
        if isinstance(parsed, list):
            return [g.strip() for g in parsed]
        if isinstance(parsed, str):
            return [s.strip() for s in parsed.split(",")]
    except Exception:
        return [s.strip() for s in genre_str.split(",")]
    return []


def get_paintings_list(params: dict) -> tuple[list[dict], int]:
    """
    Returns a tuple (results, total_pages) according to the same rules as your paintings_list function.
    params expects a dictionary with keys:
       page, sort, order, search, genre, year, artist, page_size
    """
    # 1) Read parameters
    page = int(params.get("page", 1))
    sort = params.get("sort", "filename")
    order = params.get("order", "asc")
    search = params.get("search", "")
    genre = params.get("genre", "")
    year = params.get("year", "")
    artist_name = params.get("artist", "")

    try:
        page_size = int(params.get("page_size", "8"))
    except ValueError:
        page_size = 8
    if page_size <= 0:
        page_size = 8

    # 2) Base queryset
    queryset = Painting.objects.select_related("artist").all()

    # 3) Filter by search
    if search:
        queryset = queryset.filter(
            Q(filename__icontains=search) |
            Q(genre__icontains=search) |
            Q(artist__name__icontains=search)
        )

    # 4) Filter by year and artist
    if year:
        queryset = queryset.filter(year=year)
    if artist_name:
        queryset = queryset.filter(artist__name=artist_name)

    # 5) Convert to list for Python-level genre filtering
    all_paintings = list(queryset)
    if genre:
        filtered = []
        for p in all_paintings:
            parsed_genres = parse_genre_field(p.genre)
            if genre in parsed_genres:
                filtered.append(p)
        all_paintings = filtered

    # 6) Sorting
    valid_sort_fields = ["filename", "year", "artist_name", "genre", "id"]
    if sort not in valid_sort_fields:
        sort = "filename"
    reverse_sort = (order.lower() == "desc")

    if sort == "artist_name":
        all_paintings.sort(
            key=lambda p: (p.artist.name if p.artist else ""),
            reverse=reverse_sort
        )
    elif sort == "genre":
        all_paintings.sort(
            key=lambda p: parse_genre_field(p.genre)[0] if parse_genre_field(p.genre) else "",
            reverse=reverse_sort
        )
    else:
        all_paintings.sort(
            key=lambda p: getattr(p, sort) if getattr(p, sort) is not None else "",
            reverse=reverse_sort
        )

    # 7) Pagination
    total_count = len(all_paintings)
    total_pages = ceil(total_count / page_size) if total_count > 0 else 1
    if page < 1:
        page = 1
    if page > total_pages:
        page = total_pages

    start_index = (page - 1) * page_size
    end_index = start_index + page_size
    paintings_page = all_paintings[start_index:end_index]

    # 8) Build result (list of dicts)
    results = []
    for p in paintings_page:
        results.append({
            "id": p.id,
            "filename": p.filename,
            "genre": p.genre,
            "name": p.name,
            "width": p.width,
            "height": p.height,
            "genre_count": p.genre_count,
            "year": p.year,
            "artist_id": p.artist.id if p.artist else None,
            "artist_name": p.artist.name if p.artist else None,
            "artist_years": p.artist.years if p.artist else None
        })

    return results, total_pages


def get_painting_detail(pk: int) -> dict:
    """
    Returns a dictionary with detailed information for the painting with the given PK.
    If the record is not found, get_object_or_404 will raise Http404.
    """
    painting = get_object_or_404(Painting.objects.select_related("artist"), pk=pk)
    data = {
        "id": painting.id,
        "filename": painting.filename,
        "genre": painting.genre,
        "name": painting.name,
        "detailed_caption": painting.detailed_caption,
        "width": painting.width,
        "height": painting.height,
        "genre_count": painting.genre_count,
        "year": painting.year,
        "artist_id": painting.artist.id if painting.artist else None,
        "artist_name": painting.artist.name if painting.artist else None,
        "artist_years": painting.artist.years if painting.artist else None
    }
    return data


def get_filter_options(params: dict) -> dict:
    """
    Returns a JSON-like dictionary with unique genres, years, and artists
    considering the current filters (search, genre, year, artist).
    """
    search = params.get("search", "")
    genre = params.get("genre", "")
    year = params.get("year", "")
    artist_name = params.get("artist", "")

    # 1) Base queryset
    queryset = Painting.objects.select_related("artist").all()

    # 2) Filter by search
    if search:
        queryset = queryset.filter(
            Q(filename__icontains=search) |
            Q(genre__icontains=search) |
            Q(artist__name__icontains=search)
        )

    # 3) Filter by year and artist
    if year:
        queryset = queryset.filter(year=year)
    if artist_name:
        queryset = queryset.filter(artist__name=artist_name)

    # 4) Convert to list and filter by genre at the Python level
    all_paintings = list(queryset)
    if genre:
        filtered = []
        for p in all_paintings:
            parsed_genres = parse_genre_field(p.genre)
            if genre in parsed_genres:
                filtered.append(p)
        all_paintings = filtered

    # 5) Collect unique values
    genres_set = set()
    years_set = set()
    artists_set = set()

    for p in all_paintings:
        parsed_genres = parse_genre_field(p.genre)
        for g in parsed_genres:
            if g:
                genres_set.add(g)
        if p.year:
            years_set.add(p.year)
        if p.artist and p.artist.name:
            artists_set.add(p.artist.name)

    return {
        "genres": sorted(genres_set),
        "years": sorted(years_set),
        "artists": sorted(artists_set),
    }
