import React, { useState, useEffect } from 'react';

const DesignFilesGallery = ({ designFiles, openImageModal }) => {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedImage, setSelectedImage] = useState(null);
  const [zoomLevel, setZoomLevel] = useState(1);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  // Filter images based on search term
  const filteredImages = designFiles.filter(image =>
    image.filename.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
    const handleKeyPress = (e) => {
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
  }, [selectedImage, currentImageIndex, filteredImages]);

  return (
    <div>
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-xl font-semibold text-gray-900">Design Files</h3>
        <div className="relative">
          <input
            type="text"
            placeholder="Search design files..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          />
          <svg
            className="absolute left-3 top-2.5 h-5 w-5 text-gray-400"
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

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        {filteredImages.map((image, index) => (
          <div key={index} className="card overflow-hidden group">
            <div className="aspect-square overflow-hidden">
              <img
                src={image.path}
                alt={image.filename}
                onClick={() => openZoomModal(image, index)}
                className="w-full h-full object-cover cursor-pointer transition-transform duration-300 group-hover:scale-105"
              />
            </div>
            <div className="p-4">
              <h3 className="font-semibold text-gray-900 mb-2 line-clamp-2">{image.filename}</h3>
              <p className="text-sm text-gray-500">Design File</p>
            </div>
          </div>
        ))}
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
                src={selectedImage.path}
                alt={selectedImage.filename}
                style={{
                  transform: `scale(${zoomLevel})`,
                  transformOrigin: 'center',
                  transition: 'transform 0.2s ease-in-out'
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
    </div>
  );
};

export default DesignFilesGallery; 