// src/components/FilterBar.js
import React from 'react';

function FilterBar({
  searchText,
  onSearchChange,
  selectedGenre,
  onGenreChange,
  selectedYear,
  onYearChange,
  selectedArtist,
  onArtistChange,
  genres,
  years,
  artists
}) {
  return (
    <div>
      {/* Search input */}
      <div className="mb-3">
        <input
          className="form-control"
          placeholder="Search artworks..."
          value={searchText}
          onChange={onSearchChange}
        />
      </div>

      {/* Filters */}
      <div className="row mb-3">
        <div className="col-md-4">
          <label>Genre:</label>
          <select className="form-select" value={selectedGenre} onChange={onGenreChange}>
            <option value="">All</option>
            {genres.map(g => (
              <option key={g} value={g}>{g}</option>
            ))}
          </select>
        </div>
        <div className="col-md-4">
          <label>Year:</label>
          <select className="form-select" value={selectedYear} onChange={onYearChange}>
            <option value="">All</option>
            {years.map(y => (
              <option key={y} value={y}>{y}</option>
            ))}
          </select>
        </div>
        <div className="col-md-4">
          <label>Artist:</label>
          <select className="form-select" value={selectedArtist} onChange={onArtistChange}>
            <option value="">All</option>
            {artists.map(a => (
              <option key={a} value={a}>{a}</option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

export default FilterBar;
