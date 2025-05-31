// src/pages/SmartSearchPage.js
import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../GalleryPage.css'
import { normalizeGenre } from '../utils/normalizeGenre'

export default function SmartSearchPage() {
  const location = useLocation()

  // — поисковый ввод + режим VQA и сортировка по caption
  const [vectorQuery, setVectorQuery]     = useState('')
  const [useVQA, setUseVQA]               = useState(false)
  const [sortByCaption, setSortByCaption] = useState(false)
  const [captionWeight, setCaptionWeight] = useState(0) // 0…1

  // — полные и отфильтрованные результаты
  const [similarPaintings, setSimilarPaintings]   = useState([])
  const [filteredPaintings, setFilteredPaintings] = useState([])

  // — опции фильтров
  const [genres, setGenres]   = useState([])
  const [years, setYears]     = useState([])
  const [artists, setArtists] = useState([])

  // — выбранные фильтры
  const [selGenre, setSelGenre]   = useState('')
  const [selYear, setSelYear]     = useState('')
  const [selArtist, setSelArtist] = useState('')

  const [loading, setLoading] = useState(false)

  // при маунте: загружаем сохранённое состояние
  useEffect(() => {
    const saved = sessionStorage.getItem('smartSearchState')
    if (saved) {
      const {
        vectorQuery: q,
        useVQA: v,
        sortByCaption: s,
        captionWeight: w,
        results,
        selGenre: g,
        selYear: y,
        selArtist: a
      } = JSON.parse(saved)
      setVectorQuery(q)
      setUseVQA(v)
      setSortByCaption(s)
      setCaptionWeight(w ?? 0)
      setSimilarPaintings(results)
      setSelGenre(g)
      setSelYear(y)
      setSelArtist(a)
    }
  }, [])
  // При переключении VQA — сбрасываем сортировку по подписи
  useEffect(() => {
    if (useVQA) {
      setSortByCaption(false)
    }
  }, [useVQA])
  // сохраняем в sessionStorage при изменении важных состояний
  useEffect(() => {
    sessionStorage.setItem(
      'smartSearchState',
      JSON.stringify({
        vectorQuery,
        useVQA,
        sortByCaption,
        captionWeight,
        results: similarPaintings,
        selGenre,
        selYear,
        selArtist
      })
    )
  }, [
    vectorQuery,
    useVQA,
    sortByCaption,
    captionWeight,
    similarPaintings,
    selGenre,
    selYear,
    selArtist
  ])
 const [hasSearched, setHasSearched] = useState(false)
  const [lastSearchedQuery, setLastSearchedQuery] = useState('')

  // --- 1) Smart search + подгрузка деталей ---
  const doSearch = async () => {
    if (!vectorQuery.trim()) {
      alert('Введите запрос!')
      return
    }
    setLoading(true)
    setHasSearched(true)
    setLoading(true)
    setLastSearchedQuery(vectorQuery)
    try {
      const endpoint = useVQA
        ? 'http://147.175.106.196:60000/search_similar_paintings_clip_vqa/'
        : 'http://147.175.106.196:60000/search_similar_clip/'
      const resp = await fetch(endpoint, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          query: vectorQuery,
          sort_by_caption: sortByCaption,
          caption_weight: sortByCaption ? captionWeight : 0
        })
      })
      const data = await resp.json()
      const raw = data.results || []

      // дополняем деталями и унифицируем поле distance
      const enriched = await Promise.all(
        raw.map(async item => {
          const detail = await fetch(
            `http://147.175.106.196:60000/paintings/${item.id}/`
          ).then(r => r.json())
          const distance = item.image_distance
          return { ...detail, distance }
        })
      )

      setSimilarPaintings(enriched)
      setSelGenre(''); setSelYear(''); setSelArtist('')
    } catch (err) {
      console.error(err)
      setSimilarPaintings([])
    } finally {
      setLoading(false)
    }
  }

  // --- 2) локальная фильтрация по жанру/году/художнику ---
  useEffect(() => {
    const f = similarPaintings.filter(p => {
      const arr = normalizeGenre(p.genre)
      const okG = !selGenre  || arr.includes(selGenre)
      const okY = !selYear   || String(p.year) === selYear
      const okA = !selArtist || p.artist_name === selArtist
      return okG && okY && okA
    })
    setFilteredPaintings(f)
  }, [similarPaintings, selGenre, selYear, selArtist])

  // --- 3) обновление опций селектов из отфильтрованного списка ---
  useEffect(() => {
    const gSet = new Set()
    const ySet = new Set()
    const aSet = new Set()
    filteredPaintings.forEach(p => {
      normalizeGenre(p.genre).forEach(g => gSet.add(g))
      if (p.year != null) ySet.add(p.year)
      if (p.artist_name) aSet.add(p.artist_name)
    })
    setGenres([...gSet])
    setYears([...ySet].sort((a, b) => a - b))
    setArtists([...aSet])
  }, [filteredPaintings])

  return (
    <div className="container my-4">
      {/* === INPUT & OPTIONS === */}
      <div className="mb-3 d-flex gap-2 align-items-center">
        <input
          className="form-control"
          placeholder="Smart search..."
          value={vectorQuery}
          onChange={e => setVectorQuery(e.target.value)}
        />

        <div className="form-check">
          <input
            id="vqa"
            type="checkbox"
            className="form-check-input"
            checked={useVQA}
            onChange={e => setUseVQA(e.target.checked)}
          />
          <label htmlFor="vqa" className="form-check-label">
            Use VQA
          </label>
        </div>

{/* Показываем только если VQA выключен */}
        {!useVQA && (
          <div className="form-check">
            <input
              id="sortCaption"
              type="checkbox"
              className="form-check-input"
              checked={sortByCaption}
              onChange={e => setSortByCaption(e.target.checked)}
            />
            <label htmlFor="sortCaption" className="form-check-label">
              Sort by AI Description
            </label>
          </div>
        )}

        {sortByCaption && (
          <div className="d-flex align-items-center gap-2">
            <label htmlFor="captionWeight" className="mb-0">
              Image: {(100 - captionWeight * 100).toFixed(0)}%,
              Description: {(captionWeight * 100).toFixed(0)}%
            </label>
            <input
              id="captionWeight"
              type="range"
              min="0"
              max="1"
              step="0.01"
              className="form-range"
              style={{ width: 150 }}
              value={captionWeight}
              onChange={e => setCaptionWeight(+e.target.value)}
            />
          </div>
        )}

        <button className="btn btn-secondary" onClick={doSearch}>
          Search
        </button>
      </div>

      {/* === FILTERS === */}
      <div className="row mb-3">
        <div className="col-md-4">
          <label>Genre:</label>
          <select
            className="form-select"
            value={selGenre}
            onChange={e => setSelGenre(e.target.value)}
          >
            <option value="">All</option>
            {genres.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
        <div className="col-md-4">
          <label>Year:</label>
          <select
            className="form-select"
            value={selYear}
            onChange={e => setSelYear(e.target.value)}
          >
            <option value="">All</option>
            {years.map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div className="col-md-4">
          <label>Artist:</label>
          <select
            className="form-select"
            value={selArtist}
            onChange={e => setSelArtist(e.target.value)}
          >
            <option value="">All</option>
            {artists.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
      </div>

      {/* === LOADER === */}
      {loading && (
        <div className="text-center my-5">
          <div className="spinner-border" role="status" />
        </div>
      )}

      {/* === RESULTS === */}
      {!loading && filteredPaintings.length > 0 && (
        <div className="row">
          {filteredPaintings.map(p => (
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
                  <small>Dist: {p.distance?.toFixed(3)}</small>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* === EMPTY STATES === */}
      {!loading && similarPaintings.length > 0 && filteredPaintings.length === 0 && (
        <div className="text-center py-5">
          <h5>No results after filtering</h5>
        </div>
      )}
      {!loading && similarPaintings.length === 0 && !hasSearched && (
        <div className="text-center py-5">
          <h5>Type in the query and click "Search"</h5>
        </div>
      )}
      {!loading && similarPaintings.length > 0 && filteredPaintings.length === 0 && (
        <div className="text-center py-5">
          <h5>Nothing found after filtering</h5>
        </div>
      )}
      {!loading && similarPaintings.length === 0 && hasSearched && (
        <div className="text-center py-5">
          <h5>Nothing found for the query "{lastSearchedQuery}"</h5>
        </div>
      )}
    </div>
  )
}
