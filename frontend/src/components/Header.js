import React from 'react';
import { Link } from 'react-router-dom';
import './Header.css';

const Header = () => {
  return (
    <header className="header">
      <div className="container">
        <Link to="/" className="logo">
          <h1>Etsy Seller Automaker</h1>
        </Link>
        <nav className="nav">
          <Link to="/" className="nav-link">Home</Link>
          <Link to="/mask-creator" className="nav-link">Mask Creator</Link>
          <a 
            href="https://developer.etsy.com/documentation/essentials/authentication" 
            target="_blank" 
            rel="noopener noreferrer" 
            className="nav-link"
          >
            Documentation
          </a>
        </nav>
      </div>
    </header>
  );
};

export default Header; 