// src/components/SmartSearchFilters.js

import React from 'react'

export default function SmartSearchFilters({
  selGenre,
  setSelGenre,
  selYear,
  setSelYear,
  selArtist,
  setSelArtist,
  genres,
  years,
  artists
}) {
  return (
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
  )
}
