// src/hooks/useGalleryData.js

import { useState, useEffect } from 'react';

export function useGalleryData({ page, sortBy, sortOrder, searchText, selectedGenre, selectedYear, selectedArtist, pageSize }) {
  const [paintings, setPaintings] = useState([]);
  const [totalPages, setTotalPages] = useState(1);
  const [genres, setGenres]   = useState([]);
  const [years, setYears]     = useState([]);
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(false);

  // Функция загрузки списка картин (fetchPaintings)
  const fetchPaintings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({
        page,
        sort: sortBy,
        order: sortOrder,
        search: searchText,
        page_size: pageSize
      });
      if (selectedGenre)  params.append('genre',  selectedGenre);
      if (selectedYear)   params.append('year',   selectedYear);
      if (selectedArtist) params.append('artist', selectedArtist);

      const resp = await fetch(`http://147.175.106.196:60000/paintings/?${params}`);
      const data = await resp.json();
      setPaintings(data.results);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Функция загрузки опций фильтров (fetchFilterOptions)
  const fetchFilterOptions = async () => {
    try {
      const params = new URLSearchParams({ search: searchText });
      if (selectedGenre)  params.append('genre',  selectedGenre);
      if (selectedYear)   params.append('year',   selectedYear);
      if (selectedArtist) params.append('artist', selectedArtist);

      const resp = await fetch(`http://147.175.106.196:60000/filter-options/?${params}`);
      const data = await resp.json();
      setGenres(data.genres || []);
      setYears(data.years || []);
      setArtists(data.artists || []);
    } catch (err) {
      console.error(err);
    }
  };

  // Эффекты, похожие на ваши useEffect’ы в оригинале
  useEffect(() => {
    fetchPaintings();
  }, [page, sortBy, sortOrder, searchText, selectedGenre, selectedYear, selectedArtist, pageSize]);

  useEffect(() => {
    fetchFilterOptions();
  }, [searchText, selectedGenre, selectedYear, selectedArtist]);

  return {
    paintings,
    totalPages,
    genres,
    years,
    artists,
    loading,
    refetch: fetchPaintings // если понадобится ручной триггер
  };
}
