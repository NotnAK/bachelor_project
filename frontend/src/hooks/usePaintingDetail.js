// src/hooks/usePaintingDetail.js

import { useState, useEffect } from 'react';

export function usePaintingDetail(id) {
  const [painting, setPainting] = useState(null);

  useEffect(() => {
    fetch(`http://147.175.106.196:60000/paintings/${id}/`)
      .then(r => r.json())
      .then(setPainting)
      .catch(console.error);
  }, [id]);

  return painting;
}
