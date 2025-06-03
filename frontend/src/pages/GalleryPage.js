// src/pages/GalleryPage.js
import React, { useState, useEffect } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../GalleryPage.css';

import FilterBar from '../components/FilterBar';
import PaintingGrid from '../components/PaintingGrid';
import PaginationBar from '../components/PaginationBar';
import { useGalleryData } from '../hooks/useGalleryData';

function GalleryPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const query = new URLSearchParams(location.search);

  // 1) Читаем начальные значения из URL
  const [page, setPage]                     = useState(+query.get('page')      || 1);
  const [searchText, setSearchText]         = useState(query.get('search')    || '');
  const [selectedGenre, setSelectedGenre]   = useState(query.get('genre')     || '');
  const [selectedYear, setSelectedYear]     = useState(query.get('year')      || '');
  const [selectedArtist, setSelectedArtist] = useState(query.get('artist')    || '');
  const [sortBy, setSortBy]                 = useState(query.get('sort')      || 'artist_name');
  const [sortOrder, setSortOrder]           = useState(query.get('order')     || 'asc');
  const [pageSize, setPageSize]             = useState(+query.get('page_size')|| 10);

  // 2) Вызываем хук, который возвращает данные и стейты
  const {
    paintings,
    totalPages,
    genres,
    years,
    artists,
    loading
  } = useGalleryData({
    page,
    sortBy,
    sortOrder,
    searchText,
    selectedGenre,
    selectedYear,
    selectedArtist,
    pageSize
  });

  // 3) Синхронизация URL при изменении фильтров/страницы
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchText)     params.set('search', searchText);
    if (selectedGenre)  params.set('genre', selectedGenre);
    if (selectedYear)   params.set('year', selectedYear);
    if (selectedArtist) params.set('artist', selectedArtist);
    if (sortBy !== 'artist_name') params.set('sort', sortBy);
    if (sortOrder !== 'asc')      params.set('order', sortOrder);
    if (pageSize !== 10)          params.set('page_size', String(pageSize));
    if (page !== 1)               params.set('page', String(page));
    navigate(`?${params.toString()}`, { replace: true });
  }, [page, searchText, selectedGenre, selectedYear, selectedArtist, sortBy, sortOrder, pageSize, navigate]);

  // 4) Обработчики изменения полей
  const resetPage = () => setPage(1);
  const handleSearchChange   = e => { setSearchText(e.target.value); resetPage(); };
  const handleGenreChange    = e => { setSelectedGenre(e.target.value); resetPage(); };
  const handleYearChange     = e => { setSelectedYear(e.target.value); resetPage(); };
  const handleArtistChange   = e => { setSelectedArtist(e.target.value); resetPage(); };
  const handlePageChange     = n => { if (n >= 1 && n <= totalPages) setPage(n); };
  const handlePageSizeChange = e => { setPageSize(+e.target.value); resetPage(); };

  return (
    <div className="container my-4">
      {/* 5) Рендерим FilterBar */}
      <FilterBar
        searchText={searchText}
        onSearchChange={handleSearchChange}
        selectedGenre={selectedGenre}
        onGenreChange={handleGenreChange}
        selectedYear={selectedYear}
        onYearChange={handleYearChange}
        selectedArtist={selectedArtist}
        onArtistChange={handleArtistChange}
        genres={genres}
        years={years}
        artists={artists}
      />

      {/* 6) Рендерим Pagination сверху */}
      <PaginationBar
        page={page}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        pageSize={pageSize}
        onPageSizeChange={handlePageSizeChange}
      />

      {/* 7) Рендерим саму сетку (или загрузчик) */}
      <PaintingGrid paintings={paintings} loading={loading} />

      {/* 8) Пагинация снизу */}
      <PaginationBar
        page={page}
        totalPages={totalPages}
        onPageChange={handlePageChange}
        pageSize={pageSize}
        onPageSizeChange={handlePageSizeChange}
      />
    </div>
  );
}

export default GalleryPage;
