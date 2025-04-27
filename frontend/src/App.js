// src/App.js
import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Header from './components/Header';
import GalleryPage from './pages/GalleryPage';
import SmartSearchPage from './pages/SmartSearchPage';
import PaintingDetailPage from './pages/PaintingDetailPage';

function App() {
  return (
    <>
      <Header />
      <Routes>
        <Route path="/"       element={<GalleryPage />} />
        <Route path="/smart"  element={<SmartSearchPage />} />
        <Route path="/painting/:id" element={<PaintingDetailPage />} />
      </Routes>
    </>
  );
}

export default App;
