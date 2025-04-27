import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import { Fancybox } from "@fancyapps/ui";
import "@fancyapps/ui/dist/fancybox/fancybox.css";
import '../GalleryPage.css'; // тут .img-detail-preview
import { normalizeGenre } from '../utils/normalizeGenre'
export default function PaintingDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [painting, setPainting] = useState(null);

  useEffect(() => {
    fetch(`http://147.175.106.196:60000/paintings/${id}/`)
      .then(r => r.json())
      .then(setPainting)
      .catch(console.error);
  }, [id]);

  useEffect(() => {
    if (painting) Fancybox.bind("[data-fancybox]", {});
    return () => { Fancybox.unbind("[data-fancybox]"); Fancybox.close(); };
  }, [painting]);

  if (!painting) {
    return <div className="container text-center my-5">Loading...</div>;
  }

  const imageUrl = `http://147.175.106.196:60000/media/extracted_paintings/${painting.filename}`;
  const cleanedGenres = normalizeGenre(painting.genre).join(', ')
  return (
    <div className="container my-5">
      <button
        className="btn btn-secondary mb-3"
        onClick={() => navigate(-1)}
      >
        ← Back
      </button>

      <div className="card">
        <div className="position-relative bg-light text-center p-3">
          {/* обёртка <a> для клика по картинке */}
          <a href={imageUrl} data-fancybox="gallery" data-caption={painting.name}>
            <img
              src={imageUrl}
              alt={painting.name}
              className="img-detail-preview mb-2"
            />
          </a>
        </div>
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
      </div>
    </div>
  );
}
