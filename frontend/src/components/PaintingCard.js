// src/components/PaintingCard.js
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import {API_URL} from "../config";

function PaintingCard({ painting }) {
  const location = useLocation();

  return (
    <div className="col-md-3 col-sm-6 mb-4">
      <div className="card h-100 shadow-sm">
        <Link to={`/painting/${painting.id}${location.search}`}>
          <img
            src={`${API_URL}/media/extracted_paintings/${painting.filename}`}
            alt={painting.name}
            className="card-img-top img-preview"
          />
        </Link>
        <div className="card-body p-2">
          <h6 className="text-truncate mb-1">{painting.name}</h6>
          <small>{painting.artist_name} • {painting.year}</small>
        </div>
      </div>
    </div>
  );
}

export default PaintingCard;
