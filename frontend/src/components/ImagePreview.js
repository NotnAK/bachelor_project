// src/components/ImagePreview.js

import React, { useEffect } from 'react';
import { Fancybox } from "@fancyapps/ui";
import "@fancyapps/ui/dist/fancybox/fancybox.css";
function ImagePreview({ imageUrl, caption }) {
  useEffect(() => {
    Fancybox.bind("[data-fancybox]", {});
    return () => {
      Fancybox.unbind("[data-fancybox]");
      Fancybox.close();
    };
  }, []);

  return (
    <div className="position-relative bg-light text-center p-3">
      <a href={imageUrl} data-fancybox="gallery" data-caption={caption}>
        <img
          src={imageUrl}
          alt={caption}
          className="img-detail-preview mb-2"
        />
      </a>
    </div>
  );
}

export default ImagePreview;
