// src/pages/SmartSearchPage.js

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../GalleryPage.css'
import { normalizeGenre } from '../utils/normalizeGenre'

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
  const [showClassFilter, setShowClassFilter]             = useState(false)
  const [classFilterInput, setClassFilterInput]           = useState("")   // введённая пользователем строка (например, "dog woman child")
  const [classFilterList, setClassFilterList]             = useState([])   // разобранный массив уникальных классов (max 4)
  const [isApplyingClassFilter, setIsApplyingClassFilter] = useState(false) // индикатор, что запрос к /filter_by_detected_classes/ выполняется

  const [hasSearched, setHasSearched] = useState(false)
  const [lastSearchedQuery, setLastSearchedQuery] = useState('')

  // при маунте: загружаем сохранённое состояние (если нужно)
   // при маунте: загружаем сохранённое состояние, включая filteredPaintings и class‐filter
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
          classFilterInput: cfi,
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
        setClassFilterInput(cfi ?? "")
        setClassFilterList(cfl ?? [])
      } catch (e) {
        console.warn("Не удалось распарсить smartSearchState из sessionStorage:", e)
      }
    }
    // После того, как всё восстановили, отмечаем, что инициализация завершена
    setIsInitialized(true)
  }, [])



  // При переключении VQA — сбрасываем сортировку по подписи
  useEffect(() => {
    if (useVQA) {
      setSortByCaption(false)
    }
  }, [useVQA])

  // сохраняем в sessionStorage при изменении важных состояний
   // сохраняем в sessionStorage при изменении всех «важных» состояний,
  // включая class‐filter и уже полученный filteredPaintings
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
        showClassFilter,                   // показывать или скрывать блок class‐filter
        classFilterInput,                  // текст, который был введён в поле class‐filter
        classFilterList                    // разобранный массив классов (max 4)
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
    classFilterInput,
    classFilterList
  ])


  // ================================
  // Функция для отправки запроса на фильтрацию по детектированным классам
  // ================================
  const applyClassFilter = async () => {
    // 1) Разбираем введённую пользователем строку в массив до 4 уникальных классов
    let arr = classFilterInput
      .split(/[;\s,]+/)           // разделяем по любому из символов: ;  или пробел, или запятая
      .map(x => x.trim().toLowerCase())
      .filter(x => x.length > 0)

    arr = Array.from(new Set(arr)).slice(0, 4)  // убираем дубликаты и оставляем максимум 4
    setClassFilterList(arr)

    if (arr.length === 0) {
      // Если пользователь ничего не ввёл (или удалил ввод), то сбрасываем фильтр:
      setFilteredPaintings(similarPaintings)
      return
    }

    // 2) Собираем все ID текущих картин из similarPaintings
    const allIds = similarPaintings.map(p => p.id)

    setIsApplyingClassFilter(true) // включаем индикатор загрузки

    try {
      const resp = await fetch("http://147.175.106.196:60000/filter_by_detected_classes/", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          ids: allIds,
          classes: arr
        })
      })
      const data = await resp.json()
      const passedIds = data.ids || []

      // 3) Отфильтровываем similarPaintings, оставляя только те, чей id вернулся из backend
      const afterClassFilter = similarPaintings.filter(p => passedIds.includes(p.id))
      setFilteredPaintings(afterClassFilter)
    } catch (err) {
      console.error("Error while applying class filter:", err)
    } finally {
      setIsApplyingClassFilter(false)
    }
  }

  // --- 1) Smart search + подгрузка деталей ---
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
    setClassFilterInput('')
    setClassFilterList([])
    setShowClassFilter(false)
    setFilteredPaintings([])        // очищаем предыдущие отфильтрованные
    setSimilarPaintings([])         // (опционально) очищаем, чтобы не мелькали старые

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
          const distance = item.image_distance ?? item.distance
          return { ...detail, distance }
        })
      )

      // Устанавливаем новые full-результаты и сбрасываем отфильтрованные
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

  // --- 2) локальная фильтрация по жанру/году/художнику (+ classFilterList) ---
  useEffect(() => {
    // Если ещё не дошли до инициализации из sessionStorage – не фильтруем
    if (!isInitialized) {
      return
    }

    // Иначе – применяем фильтр поверх (genre/year/artist + class-filter)
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
        {/* Поле ввода умного поиска */}
        <input
          className="form-control"
          placeholder="Smart search..."
          value={vectorQuery}
          onChange={e => setVectorQuery(e.target.value)}
        />

        {/* Checkbox «Use VQA» */}
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

        {/* Если сортировка по подписи включена, показываем ползунок веса */}
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

        {/* Кнопка «Search»: сбрасывает все фильтры и отправляет новый запрос */}
        <button className="btn btn-secondary btn-sm" onClick={doSearch}>
          Search
        </button>

        {/* Кнопка «Filter by Detected Classes» (компактная) */}
        <button
          className="btn btn-outline-primary btn-sm"
          onClick={() => setShowClassFilter(prev => !prev)}
        >
          {showClassFilter ? "Hide Class Filter" : "Filter by Detected Classes"}
        </button>
      </div>

      {/* === Блок фильтрации по классам (появляется, когда showClassFilter=true) === */}
      {showClassFilter && (
        <div className="mb-3 d-flex gap-2 align-items-center">
          <input
            type="text"
            className="form-control"
            placeholder="Введите до 4 классов (через пробел, ; или ,)"
            value={classFilterInput}
            onChange={e => setClassFilterInput(e.target.value)}
          />
          <button
            className="btn btn-primary btn-sm"
            disabled={isApplyingClassFilter}
            onClick={applyClassFilter}
          >
            {isApplyingClassFilter ? (
              <span className="spinner-border spinner-border-sm" role="status" />
            ) : (
              "Apply"
            )}
          </button>
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
    </div>
  )
}
