// src/components/SmartSearchResults.js

import React from 'react'
import { Link } from 'react-router-dom'
import {API_URL} from "../config";

export default function SmartSearchResults({ filteredPaintings, location }) {
  return (
    <div className="row">
      {filteredPaintings.map(p => (
        <div key={p.id} className="col-md-3 col-sm-6 mb-4">
          <div className="card h-100 shadow-sm">
            <Link to={`/painting/${p.id}${location.search}`}>
              <img
                src={`${API_URL}/media/extracted_paintings/${p.filename}`}
                alt={p.name}
                className="card-img-top img-preview"
              />
            </Link>
            <div className="card-body p-2">
              <h6 className="text-truncate mb-1">{p.name}</h6>
              <small>Dist: {p.distance?.toFixed(3)}</small>
            </div>
          </div>
        </div>
      ))}
    </div>
  )
}
