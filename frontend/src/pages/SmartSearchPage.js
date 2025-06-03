// src/pages/SmartSearchPage.js

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../GalleryPage.css'
import { normalizeGenre } from '../utils/normalizeGenre'

// Иконка вопроса (из react-icons)
import { FaTimesCircle } from 'react-icons/fa'

// Вносим наши новые компоненты:
import SmartSearchSearchBar from '../components/SmartSearchSearchBar'
import SmartSearchClassFilter from '../components/SmartSearchClassFilter'
import SmartSearchFilters from '../components/SmartSearchFilters'
import SmartSearchResults from '../components/SmartSearchResults'
import SmartSearchEmptyStates from '../components/SmartSearchEmptyStates'
import SmartSearchHelpModal from '../components/SmartSearchHelpModal'

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
      <SmartSearchSearchBar
        vectorQuery={vectorQuery}
        setVectorQuery={setVectorQuery}
        useVQA={useVQA}
        setUseVQA={setUseVQA}
        sortByCaption={sortByCaption}
        setSortByCaption={setSortByCaption}
        captionWeight={captionWeight}
        setCaptionWeight={setCaptionWeight}
        doSearch={doSearch}
        showClassFilter={showClassFilter}
        setShowClassFilter={setShowClassFilter}
        openHelpModal={openHelpModal}
      />

      {/* === Блок фильтрации по классам (появляется, когда showClassFilter=true) === */}
      <SmartSearchClassFilter
        showClassFilter={showClassFilter}
        newClassInput={newClassInput}
        setNewClassInput={setNewClassInput}
        handleAddClass={handleAddClass}
        classFilterList={classFilterList}
        handleRemoveClass={handleRemoveClass}
        isApplyingClassFilter={isApplyingClassFilter}
        applyClassFilter={applyClassFilter}
      />

      {/* === FILTERS: Genre / Year / Artist === */}
      <SmartSearchFilters
        selGenre={selGenre}
        setSelGenre={setSelGenre}
        selYear={selYear}
        setSelYear={setSelYear}
        selArtist={selArtist}
        setSelArtist={setSelArtist}
        genres={genres}
        years={years}
        artists={artists}
      />

      {/* === LOADER (спиннер) === */}
      {loading && (
        <div className="text-center my-5">
          <div className="spinner-border" role="status" />
        </div>
      )}

      {/* === RESULTS === */}
      {!loading && filteredPaintings.length > 0 && (
        <SmartSearchResults
          filteredPaintings={filteredPaintings}
          location={location}
        />
      )}

      {/* === EMPTY STATES === */}
      {!loading && (
        <SmartSearchEmptyStates
          loading={loading}
          similarPaintings={similarPaintings}
          filteredPaintings={filteredPaintings}
          hasSearched={hasSearched}
          lastSearchedQuery={lastSearchedQuery}
        />
      )}

      {/* === Help-модальное окно === */}
      <SmartSearchHelpModal
        showHelpModal={showHelpModal}
        closeHelpModal={closeHelpModal}
      />
    </div>
  )
}
