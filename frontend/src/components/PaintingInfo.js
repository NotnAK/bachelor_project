// src/components/PaintingInfo.js

import React from 'react';

function PaintingInfo({ painting, cleanedGenres }) {
  return (
    <div className="card-body">
      <h3 className="card-title">{painting.name}</h3>
      <p className="card-text"><strong>Artist:</strong> {painting.artist_name}</p>
      <p className="card-text"><strong>Year:</strong> {painting.year}</p>
      <p className="card-text"><strong>Genre:</strong> {cleanedGenres}</p>
      <p className="card-text"><strong>Filename:</strong> {painting.filename}</p>
      {painting.detailed_caption && (
        <p className="card-text">
          <strong>AI Description:</strong> {painting.detailed_caption}
        </p>
      )}
    </div>
  );
}

export default PaintingInfo;
