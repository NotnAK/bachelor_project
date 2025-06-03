// src/components/SmartSearchSearchBar.js

import React from 'react'
import { FaQuestionCircle } from 'react-icons/fa'

export default function SmartSearchSearchBar({
  vectorQuery,
  setVectorQuery,
  useVQA,
  setUseVQA,
  sortByCaption,
  setSortByCaption,
  captionWeight,
  setCaptionWeight,
  doSearch,
  showClassFilter,
  setShowClassFilter, openHelpModal
}) {
  return (
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
  )
}
