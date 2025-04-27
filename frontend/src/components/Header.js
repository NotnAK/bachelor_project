// src/components/Header.js
import React from 'react';
import { NavLink, Link } from 'react-router-dom';
import './Header.css';

export default function Header() {
  return (
    <nav className="navbar navbar-expand-lg navbar-dark bg-primary header-fullwidth">
      <div className="container-fluid px-4">
        <Link className="navbar-brand" to="/">ArtGallery</Link>
        <div className="navbar-nav ms-auto">
          <NavLink to="/"      end className="nav-link">Gallery</NavLink>
          <NavLink to="/smart"       className="nav-link">Smart Search</NavLink>
        </div>
      </div>
    </nav>
  );
}
