import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import ProductMockupGallery from '../../components/ProductMockupGallery';
import ProductDesignGallery from '../../components/ProductDesignGallery';
import ProductUploadModal from '../../components/ProductUploadModal';
import BackToTop from '../../components/BackToTop';

const ProductsTab = ({ isConnected, authUrl, designs, loading, error, onRefresh }) => {
  const [searchParams] = useSearchParams();
  const activeSubTab = searchParams.get('subtab') || 'productMockup';
  const [showProductUploadModal, setShowProductUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  console.log(designs);

  if (!isConnected) {
    return (
      <div className="card p-6 sm:p-8 text-center">
        <p className="text-base sm:text-lg text-gray-600 mb-6">Please connect your Etsy shop to view products</p>
        <a href={authUrl} className="btn-primary">
          Connect Shop
        </a>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
        <span className="ml-2 text-sage-600">Loading products...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{error}</p>
        <button
          onClick={onRefresh}
          className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline"
          aria-label="Retry loading products data"
        >
          Try again
        </button>
      </div>
    );
  }
  return (
    <div>
      {/* Product Mockup Tab */}
      {activeSubTab === 'productMockup' && (
        <ProductMockupGallery mockupImages={designs?.mockups || []} openImageModal={() => {}} />
      )}
      {/* Product Design Tab */}
      {activeSubTab === 'productDesign' && (
        <ProductDesignGallery designFiles={designs?.files || []} openImageModal={() => {}} />
      )}
      {/* Upload Product Tab */}
      {activeSubTab === 'upload' && (
        <div className="card p-6 sm:p-8 text-center">
          <div className="mb-6">
            <svg className="w-16 h-16 mx-auto text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
              />
            </svg>
            <h3 className="text-lg sm:text-xl font-semibold text-gray-900 mb-2">Upload New Product</h3>
            <p className="text-gray-600 text-sm sm:text-base mb-6">
              Select images to upload and create new products for your Etsy store
            </p>
          </div>
          <button
            className={`px-4 sm:px-6 py-3 rounded-lg font-medium transition-colors text-sm sm:text-base ${
              uploading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-green-500 text-white hover:bg-green-600'
            }`}
            onClick={() => setShowProductUploadModal(true)}
            disabled={uploading}
          >
            {uploading ? (
              <div className="flex items-center space-x-2">
                <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                <span>Uploading...</span>
              </div>
            ) : (
              'Select Images to Upload'
            )}
          </button>
        </div>
      )}

      {/* Template Selection Modal */}
      <ProductUploadModal
        isOpen={showProductUploadModal}
        onClose={() => setShowProductUploadModal(false)}
        onUpload={() => {
          setUploading(false);
          onRefresh();
        }}
      />

      {/* Back to Top Button */}
      <BackToTop />
    </div>
  );
};

export default ProductsTab;
