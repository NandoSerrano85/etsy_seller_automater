import React, { useState, useEffect } from 'react';
import BackToTop from './BackToTop';
import Dropdown from './Dropdown';

const DesignFilesGallery = ({ designFiles, openImageModal }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(12);
  const [viewMode, setViewMode] = useState('pagination'); // 'pagination' or 'infinite'
  const [sortOrder, setSortOrder] = useState('a-z'); // 'a-z' or 'z-a'

  // Dropdown options
  const viewOptions = [
    { value: 'pagination', label: 'Pagination' },
    { value: 'infinite', label: 'Infinite' },
  ];

  const sortOptions = [
    { value: 'a-z', label: 'A-Z' },
    { value: 'z-a', label: 'Z-A' },
  ];

  // Filter and sort images
  const filteredImages = designFiles
    .filter(image => image.filename.toLowerCase().includes(searchTerm.toLowerCase()))
    .sort((a, b) => {
      const nameA = a.filename.toLowerCase();
      const nameB = b.filename.toLowerCase();
      return sortOrder === 'a-z' ? nameA.localeCompare(nameB) : nameB.localeCompare(nameA);
    });

  // Pagination logic
  const totalPages = Math.ceil(filteredImages.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const currentImages = viewMode === 'pagination' ? filteredImages.slice(startIndex, endIndex) : filteredImages;

  // Reset to first page when search term or sort order changes
  useEffect(() => {
    setCurrentPage(1);
  }, [searchTerm, sortOrder]);

  // Infinite scroll handler
  // const handleScroll = e => {
  //   if (viewMode !== 'infinite') return;

  //   const { scrollTop, scrollHeight, clientHeight } = e.target;
  //   if (scrollTop + clientHeight >= scrollHeight - 5) {
  //     // Load more images (in this case, show all since we have all data)
  //     // In a real app, you'd fetch more data here
  //   }
  // };

  const openZoomModal = (image, index) => {
    setSelectedImage(image);
    setCurrentImageIndex(index);
    setZoomLevel(1);
  };

  const closeZoomModal = () => {
    setSelectedImage(null);
    setZoomLevel(1);
  };

  const nextImage = () => {
    if (currentImageIndex < filteredImages.length - 1) {
      setCurrentImageIndex(currentImageIndex + 1);
      setSelectedImage(filteredImages[currentImageIndex + 1]);
      setZoomLevel(1);
    }
  };

  const prevImage = () => {
    if (currentImageIndex > 0) {
      setCurrentImageIndex(currentImageIndex - 1);
      setSelectedImage(filteredImages[currentImageIndex - 1]);
      setZoomLevel(1);
    }
  };

  const zoomIn = () => {
    setZoomLevel(prev => Math.min(prev + 0.2, 3));
  };

  const zoomOut = () => {
    setZoomLevel(prev => Math.max(prev - 0.2, 0.5));
  };

  // Keyboard navigation
  useEffect(() => {
    const handleKeyPress = e => {
      if (!selectedImage) return;

      switch (e.key) {
        case 'Escape':
          closeZoomModal();
          break;
        case 'ArrowRight':
          nextImage();
          break;
        case 'ArrowLeft':
          prevImage();
          break;
        case '+':
        case '=':
          zoomIn();
          break;
        case '-':
          zoomOut();
          break;
        default:
          break;
      }
    };

    if (selectedImage) {
      document.addEventListener('keydown', handleKeyPress);
      return () => document.removeEventListener('keydown', handleKeyPress);
    }
  }, [selectedImage, currentImageIndex, filteredImages, nextImage, prevImage]); // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div>
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center mb-4 space-y-2 sm:space-y-0">
        <h3 className="text-lg sm:text-xl font-semibold text-gray-900">Design Files</h3>
        <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 w-full sm:w-auto">
          <div className="flex space-x-4 p-4">
            {/* View Mode Dropdown */}
            <Dropdown label="View" options={viewOptions} value={viewMode} onChange={setViewMode} />

            {/* Sort Order Dropdown */}
            <Dropdown label="Sort" options={sortOptions} value={sortOrder} onChange={setSortOrder} />
          </div>
          {/* Search Input */}
          <div className="relative w-full sm:w-auto">
            <input
              type="text"
              placeholder="Search design files..."
              value={searchTerm}
              onChange={e => setSearchTerm(e.target.value)}
              className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent w-full sm:w-auto text-sm sm:text-base"
            />
            <svg
              className="absolute left-3 top-2.5 h-4 w-4 sm:h-5 sm:w-5 text-gray-400"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
              />
            </svg>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 sm:gap-6">
        {currentImages.map((image, index) => (
          <div key={index} className="card overflow-hidden group">
            <div className="aspect-square overflow-hidden">
              <img
                src={image.path || image.url}
                alt={image.filename}
                onClick={() => openZoomModal(image, index)}
                className="w-full h-full object-cover cursor-pointer transition-transform duration-300 group-hover:scale-105"
                onError={e => {
                  console.error('Image failed to load:', image.path || image.url);
                  e.target.style.display = 'none';
                  e.target.nextSibling.style.display = 'flex';
                }}
                onLoad={() => {
                  console.log('Image loaded successfully:', image.path || image.url);
                }}
              />
              <div
                className="w-full h-full flex items-center justify-center bg-gray-100 text-gray-500 text-sm hidden"
                style={{ display: 'none' }}
              >
                Failed to load image
              </div>
            </div>
            <div className="p-3 sm:p-4">
              <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2 text-sm sm:text-base">{image.filename}</h3>
              <p className="text-xs sm:text-sm text-gray-500">Design File</p>
            </div>
          </div>
        ))}
      </div>

      {/* Pagination Controls */}
      {viewMode === 'pagination' && totalPages > 1 && (
        <div className="flex justify-center items-center space-x-2 mt-6">
          <button
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Previous
          </button>

          <div className="flex space-x-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }

              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-2 text-sm rounded-lg ${
                    currentPage === pageNum ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <button
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2 text-sm bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}

      {/* Results Info */}
      <div className="text-center text-sm text-gray-600 mt-4">
        Showing {startIndex + 1}-{Math.min(endIndex, filteredImages.length)} of {filteredImages.length} design files
      </div>

      {/* Zoom Modal */}
      {selectedImage && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50">
          <div className="relative max-w-4xl max-h-full p-4">
            {/* Close button */}
            <button
              onClick={closeZoomModal}
              className="absolute top-2 right-2 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>

            {/* Navigation buttons */}
            {currentImageIndex > 0 && (
              <button
                onClick={prevImage}
                className="absolute left-4 top-1/2 transform -translate-y-1/2 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            )}

            {currentImageIndex < filteredImages.length - 1 && (
              <button
                onClick={nextImage}
                className="absolute right-4 top-1/2 transform -translate-y-1/2 z-10 bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75 transition-colors"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                </svg>
              </button>
            )}

            {/* Zoom controls */}
            <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-10 flex space-x-2">
              <button
                onClick={zoomOut}
                className="bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                </svg>
              </button>
              <span className="bg-black bg-opacity-50 text-white px-3 py-2 rounded-lg text-sm">
                {Math.round(zoomLevel * 100)}%
              </span>
              <button
                onClick={zoomIn}
                className="bg-black bg-opacity-50 text-white rounded-full p-2 hover:bg-opacity-75 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
              </button>
            </div>

            {/* Image */}
            <div className="overflow-auto max-h-full">
              <img
                src={selectedImage.path || selectedImage.url}
                alt={selectedImage.filename}
                style={{
                  transform: `scale(${zoomLevel})`,
                  transformOrigin: 'center',
                  transition: 'transform 0.2s ease-in-out',
                }}
                className="max-w-full h-auto"
              />
            </div>

            {/* Image info */}
            <div className="absolute bottom-4 left-4 z-10 bg-black bg-opacity-50 text-white px-3 py-2 rounded-lg text-sm">
              {selectedImage.filename} ({currentImageIndex + 1} of {filteredImages.length})
            </div>

            {/* Keyboard shortcuts hint */}
            <div className="absolute top-4 left-4 z-10 bg-black bg-opacity-50 text-white px-3 py-2 rounded-lg text-xs">
              <div>← → Navigate | +/- Zoom | ESC Close</div>
            </div>
          </div>
        </div>
      )}

      {/* Back to Top Button */}
      <BackToTop />
    </div>
  );
};

export default DesignFilesGallery;
