// src/components/PaginationBar.js
import React from 'react';

function PaginationBar({ page, totalPages, onPageChange, pageSize, onPageSizeChange }) {
  return (
    <div className="d-flex justify-content-between align-items-center mt-3 mb-3">
      <div>
        <button
          className="btn btn-outline-primary me-2"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
        >
          Prev
        </button>
        <button
          className="btn btn-outline-primary"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
        >
          Next
        </button>
      </div>
      <div>
        <span className="me-2">Page {page} of {totalPages}</span>
        <select
          className="form-select d-inline-block"
          style={{ width: 'auto' }}
          value={pageSize}
          onChange={onPageSizeChange}
        >
          {[5, 8, 10, 20, 50, 100].map(n => (
            <option key={n} value={n}>{n}</option>
          ))}
        </select>
      </div>
    </div>
  );
}

export default PaginationBar;
