// src/pages/GalleryPage.js
import React, { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation, NavLink } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../GalleryPage.css';

function GalleryPage() {
  // роутинг и URL-параметры
  const navigate = useNavigate();
  const location = useLocation();
  const query    = new URLSearchParams(location.search);
  const [page, setPage]                   = useState(+query.get('page')      || 1);
  const [searchText, setSearchText]       = useState(query.get('search')    || '');
  const [selectedGenre, setSelectedGenre] = useState(query.get('genre')     || '');
  const [selectedYear, setSelectedYear]   = useState(query.get('year')      || '');
  const [selectedArtist, setSelectedArtist] = useState(query.get('artist')   || '');
  const [sortBy, setSortBy]               = useState(query.get('sort')      || 'artist_name');
  const [sortOrder, setSortOrder]         = useState(query.get('order')     || 'asc');
  const [pageSize, setPageSize]           = useState(+query.get('page_size')|| 10);

  // данные
  const [paintings, setPaintings] = useState([]);
  const [totalPages, setTotalPages] = useState(1);
  const [genres, setGenres]   = useState([]);
  const [years, setYears]     = useState([]);
  const [artists, setArtists] = useState([]);
  const [loading, setLoading] = useState(false);

  // 1) Fetch галереи
  const fetchPaintings = async () => {
    setLoading(true);
    try {
      const params = new URLSearchParams({ page, sort: sortBy, order: sortOrder, search: searchText, page_size: pageSize });
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

  // 2) Fetch опций фильтров
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

  // 3) Подгружаем при изменении параметров
  useEffect(() => {
    fetchPaintings();
  }, [page, sortBy, sortOrder, searchText, selectedGenre, selectedYear, selectedArtist, pageSize]);

  // 4) Подгружаем фильтры
  useEffect(() => {
    fetchFilterOptions();
  }, [searchText, selectedGenre, selectedYear, selectedArtist]);

  // 5) URL-синхронизация
  useEffect(() => {
    const params = new URLSearchParams();
    if (searchText)     params.set('search', searchText);
    if (selectedGenre)  params.set('genre', selectedGenre);
    if (selectedYear)   params.set('year', selectedYear);
    if (selectedArtist) params.set('artist', selectedArtist);
    if (sortBy !== 'artist_name') params.set('sort', sortBy);
    if (sortOrder !== 'asc')      params.set('order',sortOrder);
    if (pageSize !== 10)          params.set('page_size', String(pageSize));
    if (page !== 1)               params.set('page',      String(page));
    navigate(`?${params.toString()}`, { replace: true });
  }, [page, searchText, selectedGenre, selectedYear, selectedArtist, sortBy, sortOrder, pageSize, navigate]);

  // 6) Обработчики
  const resetPage = () => setPage(1);
  const handleSearchChange   = e => { setSearchText(e.target.value); resetPage(); };
  const handleGenreChange    = e => { setSelectedGenre(e.target.value); resetPage(); };
  const handleYearChange     = e => { setSelectedYear(e.target.value); resetPage(); };
  const handleArtistChange   = e => { setSelectedArtist(e.target.value); resetPage(); };
  const handlePageChange     = n => { if (n>=1&&n<=totalPages) setPage(n); };
  const handlePageSizeChange = e => { setPageSize(+e.target.value); resetPage(); };

  return (
    <div className="container my-4">
      {/* Поиск */}
      <div className="mb-3">
        <input
          className="form-control"
          placeholder="Search artworks..."
          value={searchText}
          onChange={handleSearchChange}
        />
      </div>

      {/* Фильтры */}
      <div className="row mb-3">
        <div className="col-md-4">
          <label>Genre:</label>
          <select className="form-select" value={selectedGenre} onChange={handleGenreChange}>
            <option value="">All</option>
            {genres.map(g => <option key={g} value={g}>{g}</option>)}
          </select>
        </div>
        <div className="col-md-4">
          <label>Year:</label>
          <select className="form-select" value={selectedYear} onChange={handleYearChange}>
            <option value="">All</option>
            {years.map(y => <option key={y} value={y}>{y}</option>)}
          </select>
        </div>
        <div className="col-md-4">
          <label>Artist:</label>
          <select className="form-select" value={selectedArtist} onChange={handleArtistChange}>
            <option value="">All</option>
            {artists.map(a => <option key={a} value={a}>{a}</option>)}
          </select>
        </div>
      </div>
      {/* Пагинация */}
      <div className="d-flex justify-content-between align-items-center mt-3 mb-3">
        <div>
          <button className="btn btn-outline-primary me-2" onClick={() => handlePageChange(page-1)} disabled={page<=1}>Prev</button>
          <button className="btn btn-outline-primary"          onClick={() => handlePageChange(page+1)} disabled={page>=totalPages}>Next</button>
        </div>
        <div>
          <span className="me-2">Page {page} of {totalPages}</span>
          <select className="form-select d-inline-block" style={{width:'auto'}} value={pageSize} onChange={handlePageSizeChange}>
            {[5,8,10,20,50,100].map(n=><option key={n} value={n}>{n}</option>)}
          </select>
        </div>
      </div>
      {/* Loader */}
      {loading && (
        <div className="text-center my-5">
          <div className="spinner-border" role="status"><span className="visually-hidden">Loading...</span></div>
        </div>
      )}

      {/* Галерея */}
      {!loading && (
        <>
          <div className="row">
            {paintings.map(p => (
              <div key={p.id} className="col-md-3 col-sm-6 mb-4">
                <div className="card h-100 shadow-sm">
                  <Link to={`/painting/${p.id}${location.search}`}>
                    <img
                      src={`http://147.175.106.196:60000/media/extracted_paintings/${p.filename}`}
                      alt={p.name}
                      className="card-img-top img-preview"
                    />
                  </Link>
                  <div className="card-body p-2">
                    <h6 className="text-truncate mb-1">{p.name}</h6>
                    <small>{p.artist_name} • {p.year}</small>
                  </div>
                </div>
              </div>
            ))}
          </div>
          {/* Если не загрузка и картин нет */}
          {!loading && paintings.length === 0 && (
            <div className="text-center py-5">
              <h5>No paintings found</h5>
            </div>
          )}
          {/* Пагинация */}
          <div className="d-flex justify-content-between align-items-center mt-3">
            <div>
              <button className="btn btn-outline-primary me-2" onClick={() => handlePageChange(page-1)} disabled={page<=1}>Prev</button>
              <button className="btn btn-outline-primary"          onClick={() => handlePageChange(page+1)} disabled={page>=totalPages}>Next</button>
            </div>
            <div>
              <span className="me-2">Page {page} of {totalPages}</span>
              <select className="form-select d-inline-block" style={{width:'auto'}} value={pageSize} onChange={handlePageSizeChange}>
                {[5,8,10,20,50,100].map(n=><option key={n} value={n}>{n}</option>)}
              </select>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

export default GalleryPage;
