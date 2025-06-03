// src/components/PaintingGrid.js
import React from 'react';
import PaintingCard from './PaintingCard';

function PaintingGrid({ paintings, loading }) {
  if (loading) {
    return (
      <div className="text-center my-5">
        <div className="spinner-border" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (!loading && paintings.length === 0) {
    return (
      <div className="text-center py-5">
        <h5>No paintings found</h5>
      </div>
    );
  }

  return (
    <div className="row">
      {paintings.map(p => (
        <PaintingCard key={p.id} painting={p} />
      ))}
    </div>
  );
}

export default PaintingGrid;
