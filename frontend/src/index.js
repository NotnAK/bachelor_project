import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import GalleryPage from "./pages/GalleryPage";
import PaintingDetailPage from "./pages/PaintingDetailPage";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Главная страница (список картин) */}
        <Route path="/" element={<GalleryPage />} />

        {/* Детальная страница для картины */}
        <Route path="/painting/:id" element={<PaintingDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App />);
