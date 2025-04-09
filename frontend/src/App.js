import React, { useState, useEffect } from "react";
import "bootstrap/dist/css/bootstrap.min.css";
import { Fancybox } from "@fancyapps/ui";
import "@fancyapps/ui/dist/fancybox/fancybox.css";
import { motion } from "framer-motion";
import "./App.css";

function App() {
  // Состояния
  const [paintings, setPaintings] = useState([]);
  const [searchText, setSearchText] = useState("");

  // Пагинация
  const [page, setPage] = useState(1);         // Текущая страница
  const [totalPages, setTotalPages] = useState(1);  // Всего страниц

  // Сортировка
  const [sortBy, setSortBy] = useState("filename"); // Поле сортировки
  const [sortOrder, setSortOrder] = useState("asc"); // asc или desc

  // Детальный просмотр
  const [selectedPainting, setSelectedPainting] = useState(null);

  useEffect(() => {
    Fancybox.bind("[data-fancybox]", {});
    return () => {
      Fancybox.destroy();
    };
  }, []);

  // Функция загрузки данных с сервера
  async function fetchPaintings(currentPage, currentSortBy, currentSortOrder, query) {
    try {
      // Формируем параметры GET
      // page=..., sort=..., order=..., search=...
      const params = new URLSearchParams({
        page: currentPage,
        sort: currentSortBy,
        order: currentSortOrder,
        search: query,   // Поиск
      });
      const url = `http://127.0.0.1:8000/paintings/?${params.toString()}`;

      const response = await fetch(url);
      const data = await response.json();

      // Ожидаем, что сервер вернет { results: [...], total_pages: N }
      setPaintings(data.results);
      setTotalPages(data.total_pages);
    } catch (error) {
      console.error("Ошибка при загрузке картин:", error);
    }
  }

  // Подгружаем данные при изменении page, sortBy, sortOrder, searchText
  useEffect(() => {
    fetchPaintings(page, sortBy, sortOrder, searchText);
  }, [page, sortBy, sortOrder, searchText]);

  // Обработка клика по картинке
  const handlePaintingClick = (painting) => {
    setSelectedPainting(painting);
  };

  // Закрытие модального окна
  const handleCloseModal = () => {
    setSelectedPainting(null);
  };

  // Функция смены страницы
  const handlePageChange = (newPage) => {
    if (newPage >= 1 && newPage <= totalPages) {
      setPage(newPage);
    }
  };

  // Смена порядка сортировки
  const handleSortChange = (e) => {
    setSortBy(e.target.value);
  };
  const handleSortOrderChange = (e) => {
    setSortOrder(e.target.value);
  };

  return (
    <div className="app-container">
      {/* Header */}
      <header className="header">
        <h1>Art Gallery</h1>
      </header>

      {/* Search Bar */}
      <motion.div
        className="search-container"
        initial={{ y: -50, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.5 }}
      >
        <input
          type="text"
          className="search-input"
          placeholder="🔍 Search for artworks or artists..."
          value={searchText}
          onChange={(e) => setSearchText(e.target.value)}
        />
      </motion.div>

      <div className="content">
        {/* Filters / Sort */}
        <motion.aside
          className="filters"
          initial={{ x: -50, opacity: 0 }}
          animate={{ x: 0, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <h4>Sort By</h4>
          <select className="form-control mb-3" value={sortBy} onChange={handleSortChange}>
            <option value="filename">Filename</option>
            <option value="year">Year</option>
            <option value="artist_name">Artist Name</option>
          </select>

          <h4>Order</h4>
          <select className="form-control mb-3" value={sortOrder} onChange={handleSortOrderChange}>
            <option value="asc">Ascending</option>
            <option value="desc">Descending</option>
          </select>

          <hr />
          <h4>Pagination</h4>
          <div>
            <button onClick={() => handlePageChange(page - 1)} disabled={page <= 1}>
              Prev
            </button>
            <span style={{ margin: "0 8px" }}>
              Page {page} of {totalPages}
            </span>
            <button onClick={() => handlePageChange(page + 1)} disabled={page >= totalPages}>
              Next
            </button>
          </div>
        </motion.aside>

        {/* Gallery */}
        <motion.div
          className="gallery-container"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.8 }}
        >
          {paintings.map((painting) => {
            const imageUrl = `http://127.0.0.1:8000/media/extracted_paintings/${painting.filename}`;
            const caption = painting.artist_name
              ? `${painting.artist_name} - ${painting.filename}`
              : painting.filename;

            return (
              <motion.div
                key={painting.id}
                className="gallery-item"
                whileHover={{ scale: 1.05 }}
                transition={{ type: "spring", stiffness: 200 }}
              >
                <div onClick={() => handlePaintingClick(painting)}>
                  <a href={imageUrl} data-fancybox="gallery" data-caption={caption}>
                    <img src={imageUrl} alt={caption} className="gallery-img" />
                  </a>
                </div>
                <div>
                  <p>Genre: {painting.genre}</p>
                  <p>Year: {painting.year}</p>
                  <p>Artist: {painting.artist_name}</p>
                </div>
              </motion.div>
            );
          })}
        </motion.div>
      </div>

      {/* Модальное окно при клике на картинку */}
      {selectedPainting && (
        <div className="modal-overlay" onClick={handleCloseModal}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{selectedPainting.filename}</h2>
            <p>Artist: {selectedPainting.artist_name}</p>
            <p>Year: {selectedPainting.year}</p>
            <p>Genre: {selectedPainting.genre}</p>
            <p>Description: {selectedPainting.description}</p>
            <p>phash: {selectedPainting.phash}</p>
            <p>Dimensions: {selectedPainting.width} x {selectedPainting.height}</p>
            <button onClick={handleCloseModal}>Close</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
