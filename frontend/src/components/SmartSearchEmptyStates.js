// src/components/SmartSearchEmptyStates.js

import React from 'react'

export default function SmartSearchEmptyStates({
  loading,
  similarPaintings,
  filteredPaintings,
  hasSearched,
  lastSearchedQuery
}) {
  return (
    <>
      {!loading && filteredPaintings.length > 0 && null}

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
      {!loading && similarPaintings.length > 0 && filteredPaintings.length === 0 && null}
      {!loading && similarPaintings.length === 0 && hasSearched && (
        <div className="text-center py-5">
          <h5>Nothing found for the query "{lastSearchedQuery}"</h5>
        </div>
      )}
    </>
  )
}
