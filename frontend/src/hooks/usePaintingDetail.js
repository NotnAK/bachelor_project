// src/hooks/usePaintingDetail.js

import { useState, useEffect } from 'react';
import {API_URL} from "../config";

export function usePaintingDetail(id) {
  const [painting, setPainting] = useState(null);

  useEffect(() => {
    fetch(`${API_URL}/paintings/${id}/`)
      .then(r => r.json())
      .then(setPainting)
      .catch(console.error);
  }, [id]);

  return painting;
}
