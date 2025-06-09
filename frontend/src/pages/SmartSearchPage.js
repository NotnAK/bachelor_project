// src/pages/SmartSearchPage.js

import React, { useState, useEffect } from 'react'
import { Link, useLocation } from 'react-router-dom'
import 'bootstrap/dist/css/bootstrap.min.css'
import '../GalleryPage.css'
import { normalizeGenre } from '../utils/normalizeGenre'

import { FaTimesCircle } from 'react-icons/fa'

import SmartSearchSearchBar from '../components/SmartSearchSearchBar'
import SmartSearchClassFilter from '../components/SmartSearchClassFilter'
import SmartSearchFilters from '../components/SmartSearchFilters'
import SmartSearchResults from '../components/SmartSearchResults'
import SmartSearchEmptyStates from '../components/SmartSearchEmptyStates'
import SmartSearchHelpModal from '../components/SmartSearchHelpModal'
import {API_URL} from "../config";

export default function SmartSearchPage() {
  const location = useLocation()

  const [isInitialized, setIsInitialized] = useState(false)


  const [vectorQuery, setVectorQuery]     = useState('')
  const [useVQA, setUseVQA]               = useState(false)
  const [sortByCaption, setSortByCaption] = useState(false)
  const [captionWeight, setCaptionWeight] = useState(0) // 0…1


  const [similarPaintings, setSimilarPaintings]   = useState([])
  const [filteredPaintings, setFilteredPaintings] = useState([])


  const [genres, setGenres]   = useState([])
  const [years, setYears]     = useState([])
  const [artists, setArtists] = useState([])


  const [selGenre, setSelGenre]   = useState('')
  const [selYear, setSelYear]     = useState('')
  const [selArtist, setSelArtist] = useState('')

  const [loading, setLoading] = useState(false)


  const [showClassFilter, setShowClassFilter]             = useState(false)
  const [newClassInput, setNewClassInput]                 = useState('')
  const [classFilterList, setClassFilterList]             = useState([])
  const [isApplyingClassFilter, setIsApplyingClassFilter] = useState(false)

  const [hasSearched, setHasSearched] = useState(false)
  const [lastSearchedQuery, setLastSearchedQuery] = useState('')


  const [showHelpModal, setShowHelpModal] = useState(false)

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

  useEffect(() => {
    if (useVQA) {
      setSortByCaption(false)
    }
  }, [useVQA])

  useEffect(() => {
    sessionStorage.setItem(
      'smartSearchState',
      JSON.stringify({
        vectorQuery,
        useVQA,
        sortByCaption,
        captionWeight,
        results: similarPaintings,
        filtered: filteredPaintings,
        selGenre,
        selYear,
        selArtist,
        showClassFilter,
        classFilterList
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

  const applyClassFilter = async () => {
    if (classFilterList.length === 0) {
      setFilteredPaintings(similarPaintings)
      return
    }

    const allIds = similarPaintings.map(p => p.id)
    setIsApplyingClassFilter(true)

    try {
      const resp = await fetch(API_URL +'/filter_by_detected_classes/', {
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

  const doSearch = async () => {
    if (!vectorQuery.trim()) {
      alert('Введите запрос!')
      return
    }
    setLoading(true)
    setHasSearched(true)
    setLastSearchedQuery(vectorQuery)

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
        ? '/search_similar_paintings_clip_vqa/'
        : '/search_similar_clip/'
      const resp = await fetch(API_URL + endpoint, {
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
            `${API_URL}/paintings/${item.id}/`
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

  const closeHelpModal = () => setShowHelpModal(false)
  const openHelpModal = () => setShowHelpModal(true)

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


  const handleRemoveClass = (cls) => {
    setClassFilterList(classFilterList.filter(c => c !== cls))
  }


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

      {/* === Class filtering block (appears when showClassFilter=true) === */}
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

      {/* === LOADER === */}
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

      {/* === Help === */}
      <SmartSearchHelpModal
        showHelpModal={showHelpModal}
        closeHelpModal={closeHelpModal}
      />
    </div>
  )
}
