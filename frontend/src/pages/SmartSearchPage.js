// src/pages/SmartSearchPage.js

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../GalleryPage.css'
import { normalizeGenre } from '../utils/normalizeGenre'

// Иконка вопроса (из react-icons)
import { FaQuestionCircle, FaTimesCircle } from 'react-icons/fa'

export default function SmartSearchPage() {
  const location = useLocation()

  // флаг, чтобы не выполнять «лишнюю» фильтрацию при первичной загрузке из sessionStorage
  const [isInitialized, setIsInitialized] = useState(false)

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

  // — выбранные фильтры (genre/year/artist)
  const [selGenre, setSelGenre]   = useState('')
  const [selYear, setSelYear]     = useState('')
  const [selArtist, setSelArtist] = useState('')

  const [loading, setLoading] = useState(false)

  // — состояния для фильтрации по классам, детектируемым Paligemma:
  //    теперь: вводим один класс за раз, нажимаем "Add" → попадает в массив classFilterList
  const [showClassFilter, setShowClassFilter]             = useState(false)
  const [newClassInput, setNewClassInput]                 = useState('')   // ввод одного класса
  const [classFilterList, setClassFilterList]             = useState([])   // массив добавленных классов (max 4)
  const [isApplyingClassFilter, setIsApplyingClassFilter] = useState(false) // индикатор, что запрос к /filter_by_detected_classes/ выполняется

  const [hasSearched, setHasSearched] = useState(false)
  const [lastSearchedQuery, setLastSearchedQuery] = useState('')

  // — состояние для показа/скрытия Help-модального окна
  const [showHelpModal, setShowHelpModal] = useState(false)

  // ───────────────────────────────────────────────────────────────
  // 1) при маунте: восстанавливаем state из sessionStorage
  // ───────────────────────────────────────────────────────────────
  useEffect(() => {
    const saved = sessionStorage.getItem('smartSearchState')
    if (saved) {
      try {
        const {
          vectorQuery: q,
          useVQA: v,
          sortByCaption: s,
          captionWeight: w,
          results,
          filtered,
          selGenre: g,
          selYear: y,
          selArtist: a,
          showClassFilter: scf,
          // вместо classFilterInput и classFilterList старого формата
          classFilterList: cfl
        } = JSON.parse(saved)

        setVectorQuery(q)
        setUseVQA(v)
        setSortByCaption(s)
        setCaptionWeight(w ?? 0)

        setSimilarPaintings(results)
        setFilteredPaintings(filtered ?? results)

        setSelGenre(g)
        setSelYear(y)
        setSelArtist(a)

        setShowClassFilter(scf ?? false)
        setClassFilterList(cfl ?? [])
      } catch (e) {
        console.warn('Не удалось распарсить smartSearchState из sessionStorage:', e)
      }
    }
    setIsInitialized(true)
  }, [])

  // ───────────────────────────────────────────────────────────────
  // 2) Если включили VQA — сбрасываем sortByCaption
  // ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (useVQA) {
      setSortByCaption(false)
    }
  }, [useVQA])

  // ───────────────────────────────────────────────────────────────
  // 3) Сохраняем в sessionStorage при изменении всех «важных» состояний
  // ───────────────────────────────────────────────────────────────
  useEffect(() => {
    sessionStorage.setItem(
      'smartSearchState',
      JSON.stringify({
        vectorQuery,
        useVQA,
        sortByCaption,
        captionWeight,
        results: similarPaintings,         // полный список «полученных» картин
        filtered: filteredPaintings,       // уже отфильтрованные (genre/year/artist + class‐filter)
        selGenre,
        selYear,
        selArtist,
        showClassFilter,
        classFilterList                    // текущий массив добавленных классов
      })
    )
  }, [
    vectorQuery,
    useVQA,
    sortByCaption,
    captionWeight,
    similarPaintings,
    filteredPaintings,
    selGenre,
    selYear,
    selArtist,
    showClassFilter,
    classFilterList
  ])

  // ───────────────────────────────────────────────────────────────
  // 4) applyClassFilter – запрос на фильтрацию по детектированным классам
  // ───────────────────────────────────────────────────────────────
  const applyClassFilter = async () => {
    if (classFilterList.length === 0) {
      // Если никто не добавлен — показываем все
      setFilteredPaintings(similarPaintings)
      return
    }

    const allIds = similarPaintings.map(p => p.id)
    setIsApplyingClassFilter(true)

    try {
      const resp = await fetch('http://147.175.106.196:60000/filter_by_detected_classes/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ids: allIds, classes: classFilterList })
      })
      const data = await resp.json()
      const passedIds = data.ids || []

      const afterClassFilter = similarPaintings.filter(p => passedIds.includes(p.id))
      setFilteredPaintings(afterClassFilter)
    } catch (err) {
      console.error('Error while applying class filter:', err)
    } finally {
      setIsApplyingClassFilter(false)
    }
  }

  // ───────────────────────────────────────────────────────────────
  // 5) doSearch – умный поиск + сброс ВСЕХ фильтров прежде, чем отправить запрос
  // ───────────────────────────────────────────────────────────────
  const doSearch = async () => {
    if (!vectorQuery.trim()) {
      alert('Введите запрос!')
      return
    }
    setLoading(true)
    setHasSearched(true)
    setLastSearchedQuery(vectorQuery)

    // При новом поиске СБРАСЫВАЕМ все фильтры и результаты
    setSelGenre('')
    setSelYear('')
    setSelArtist('')
    setClassFilterList([])
    setShowClassFilter(false)
    setNewClassInput('')
    setFilteredPaintings([])
    setSimilarPaintings([])

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

      const enriched = await Promise.all(
        raw.map(async item => {
          const detail = await fetch(
            `http://147.175.106.196:60000/paintings/${item.id}/`
          ).then(r => r.json())
          const distance = item.image_distance ?? item.distance
          return { ...detail, distance }
        })
      )

      setSimilarPaintings(enriched)
      setFilteredPaintings(enriched)
    } catch (err) {
      console.error(err)
      setSimilarPaintings([])
      setFilteredPaintings([])
    } finally {
      setLoading(false)
    }
  }

  // ───────────────────────────────────────────────────────────────
  // 6) useEffect: фильтрация по genre / year / artist поверх «class-filter»
  // ───────────────────────────────────────────────────────────────
  useEffect(() => {
    if (!isInitialized) return

    let baseList = similarPaintings
    if (classFilterList.length > 0) {
      baseList = filteredPaintings
    }

    const f = baseList.filter(p => {
      const arr = normalizeGenre(p.genre)
      const okG = !selGenre  || arr.includes(selGenre)
      const okY = !selYear   || String(p.year) === selYear
      const okA = !selArtist || p.artist_name === selArtist
      return okG && okY && okA
    })
    setFilteredPaintings(f)
  }, [isInitialized, similarPaintings, selGenre, selYear, selArtist, classFilterList])

  // ───────────────────────────────────────────────────────────────
  // 7) useEffect: обновляем опции селектов (genre/year/artist)
  // ───────────────────────────────────────────────────────────────
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

  // ───────────────────────────────────────────────────────────────
  // 8) Закрытие / открытие Help-модального
  // ───────────────────────────────────────────────────────────────
  const closeHelpModal = () => setShowHelpModal(false)
  const openHelpModal = () => setShowHelpModal(true)

  // ───────────────────────────────────────────────────────────────
  // 9) Добавление нового класса при клике «Add»
  // ───────────────────────────────────────────────────────────────
  const handleAddClass = () => {
    const cls = newClassInput.trim().toLowerCase()
    if (
      cls.length > 0 &&
      !classFilterList.includes(cls) &&
      classFilterList.length < 4
    ) {
      setClassFilterList([...classFilterList, cls])
      setNewClassInput('')
    }
  }

  // ───────────────────────────────────────────────────────────────
  // 10) Удаление класса из списка при клике на ×
  // ───────────────────────────────────────────────────────────────
  const handleRemoveClass = (cls) => {
    setClassFilterList(classFilterList.filter(c => c !== cls))
  }

  // ───────────────────────────────────────────────────────────────
  // 11) JSX-разметка
  // ───────────────────────────────────────────────────────────────
  return (
    <div className="container my-4">
      {/* === INPUT & OPTIONS === */}
      <div className="mb-3 d-flex gap-2 align-items-center">

        {/* === Help-кнопка «?» слева от поля ввода === */}
        <button
          type="button"
          className="btn btn-link text-decoration-none p-0 me-2"
          onClick={openHelpModal}
          style={{ fontSize: '1.25rem', color: '#0d6efd' }}
        >
          <FaQuestionCircle />
        </button>

        {/* Поле ввода умного поиска */}
        <input
          className="form-control"
          placeholder="Smart search..."
          value={vectorQuery}
          onChange={e => setVectorQuery(e.target.value)}
        />

        {/* Checkbox «Use VQA» */}
        <div className="form-check ms-2">
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
          <div className="form-check ms-2">
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

        {/* Если сортировка по подписи включена, показываем ползунок веса */}
        {sortByCaption && (
          <div className="d-flex align-items-center gap-2 ms-2">
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

        {/* Кнопка «Search»: сбрасывает все фильтры и отправляет новый запрос */}
        <button className="btn btn-secondary btn-sm ms-2" onClick={doSearch}>
          Search
        </button>

        {/* Кнопка «Filter by Detected Classes» (компактная) */}
        <button
          className="btn btn-outline-primary btn-sm ms-2"
          onClick={() => setShowClassFilter(prev => !prev)}
        >
          {showClassFilter ? 'Hide Class Filter' : 'Filter by Detected Classes'}
        </button>
      </div>

      {/* === Блок фильтрации по классам (появляется, когда showClassFilter=true) === */}
      {showClassFilter && (
        <div className="mb-3">
          <div className="d-flex gap-2 align-items-center">
            {/* Поле для ввода одного класса */}
            <input
              type="text"
              className="form-control form-control-sm"
              placeholder="Enter a class (e.g. dog)"
              value={newClassInput}
              onChange={e => setNewClassInput(e.target.value)}
            />
            {/* Кнопка «Add» */}
            <button
              className="btn btn-primary btn-sm"
              disabled={newClassInput.trim() === '' || classFilterList.length >= 4}
              onClick={handleAddClass}
            >
              Add
            </button>
          </div>

          {/* Список «пилочек» добавленных классов */}
          <div className="mt-2">
            {classFilterList.map((cls, idx) => (
              <span
                key={idx}
                className="badge bg-secondary text-white me-1 mb-1"
                style={{ fontSize: '0.9rem', padding: '0.4rem 0.6rem' }}
              >
                {cls}{' '}
                <FaTimesCircle
                  style={{ cursor: 'pointer' }}
                  onClick={() => handleRemoveClass(cls)}
                />
              </span>
            ))}
          </div>

          {/* Кнопка «Apply» */}
          <div className="mt-2">
            <button
              className="btn btn-success btn-sm"
              disabled={isApplyingClassFilter}
              onClick={applyClassFilter}
            >
              {isApplyingClassFilter ? (
                <span className="spinner-border spinner-border-sm" role="status" />
              ) : (
                'Apply'
              )}
            </button>
            {/* Подсказка, сколько ещё можно добавить */}
            <small className="text-muted ms-2">
              {classFilterList.length}/4 added
            </small>
          </div>
        </div>
      )}

      {/* === FILTERS: Genre / Year / Artist === */}
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
              <option key={g} value={g}>
                {g}
              </option>
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
              <option key={y} value={y}>
                {y}
              </option>
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
              <option key={a} value={a}>
                {a}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* === LOADER (спиннер) === */}
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

      {/* === Help-модальное окно === */}
      {showHelpModal && (
        <div
          className="modal d-block"
          tabIndex="-1"
          role="dialog"
          style={{ backgroundColor: 'rgba(0,0,0,0.5)' }}
        >
          <div className="modal-dialog modal-dialog-centered" role="document">
            <div className="modal-content">
              <div className="modal-header">
                <h5 className="modal-title">Help</h5>
                <button
                  type="button"
                  className="btn-close"
                  aria-label="Close"
                  onClick={closeHelpModal}
                />
              </div>
              <div className="modal-body">
                <p>
                  <strong>Search:</strong> Performs a <em>vector-based</em> search of paintings. It retrieves
                  images most similar to your query using embeddings.
                </p>
                <p>
                  <strong>Use VQA:</strong> When checked, the system will use Visual Question Answering (VQA) on
                  each candidate painting. In this mode, Paligemma answers “does this image contain &lt;your
                  query&gt;?” and only paintings with a “yes” answer will be returned.
                </p>
                <p>
                  <strong>Sort by AI Description:</strong> When unchecked, results are sorted purely by image
                  similarity. If you enable this checkbox, results will be re-ranked by combining image
                  similarity and similarity between your query and the AI-generated text description of each
                  painting. Use the slider to adjust the weight.
                </p>
                <p>
                  <strong>Filter by Detected Classes:</strong> Opens a small input field where you can type one
                  object class at a time and click “Add.” You may add up to 4 unique classes in total. The
                  added classes appear as pills with “×” to remove. After adding desired classes, click
                  “Apply” to send them to the server for filtering (only paintings containing at least 75%
                  of your specified classes will remain).
                </p>
                <p>
                  <strong>Genre / Year / Artist Filters:</strong> After receiving search results, you can further
                  narrow down the list by selecting a genre, a year, or an artist from the dropdown menus.
                </p>
              </div>
              <div className="modal-footer">
                <button
                  type="button"
                  className="btn btn-secondary btn-sm"
                  onClick={closeHelpModal}
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
