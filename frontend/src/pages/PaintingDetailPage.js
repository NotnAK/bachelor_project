// src/pages/PaintingDetailPage.js

import React from 'react';
import { useParams } from 'react-router-dom';
import 'bootstrap/dist/css/bootstrap.min.css';
import '../GalleryPage.css';

import { normalizeGenre } from '../utils/normalizeGenre';
import { usePaintingDetail } from '../hooks/usePaintingDetail';
import BackButton from '../components/BackButton';
import ImagePreview from '../components/ImagePreview';
import PaintingInfo from '../components/PaintingInfo';
import {API_URL} from "../config";

export default function PaintingDetailPage() {
  const { id } = useParams();
  const painting = usePaintingDetail(id);

  if (!painting) {
    return <div className="container text-center my-5">Loading...</div>;
  }

  const imageUrl = `${API_URL}/media/extracted_paintings/${painting.filename}`;
  const cleanedGenres = normalizeGenre(painting.genre).join(', ');

  return (
    <div className="container my-5">
      <BackButton />
      <div className="card">
        <ImagePreview imageUrl={imageUrl} caption={painting.name} />
        <PaintingInfo painting={painting} cleanedGenres={cleanedGenres} />
      </div>
    </div>
  );
}
