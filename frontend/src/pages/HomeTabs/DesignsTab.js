import React, { useState } from 'react';
import MockupsGallery from '../../components/MockupsGallery';
import DesignFilesGallery from '../../components/DesignFilesGallery';
import DesignUploadModal from '../../components/DesignUploadModal';
import BackToTop from '../../components/BackToTop';
import { FeatureGate, TierBadge } from '../../components/subscription';
import { useSubscription } from '../../hooks/useSubscription';
import { useSearchParams } from 'react-router-dom';

const DesignsTab = ({ isConnected, authUrl, designs, loading, error, onRefresh, defaultTab = 'gallery' }) => {
  const [showDesignUploadModal, setShowDesignUploadModal] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [designsTab, setDesignsTab] = useState('mockups');
  const { hasFeature, FEATURES } = useSubscription();
  // const [searchParams] = useSearchParams();
  // const activeSubTab = searchParams.get('subtab') || defaultTab;
  console.log(designs);

  if (!isConnected) {
    return (
      <div className="card p-6 sm:p-8 text-center">
        <p className="text-base sm:text-lg text-gray-600 mb-6">Please connect your Etsy shop to view designs</p>
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
        <span className="ml-2 text-sage-600">Loading designs...</span>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{error}</p>
        <button onClick={onRefresh} className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline">
          Try again
        </button>
      </div>
    );
  }
  return (
    <div>
      <div className="flex justify-end mb-4">
        <button
          className={`px-3 sm:px-4 py-2 rounded-lg font-medium transition-colors text-sm sm:text-base ${
            uploading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-green-500 text-white hover:bg-green-600'
          }`}
          onClick={() => setShowDesignUploadModal(true)}
          disabled={uploading}
        >
          {uploading ? (
            <div className="flex items-center space-x-2">
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
              <span>Uploading...</span>
            </div>
          ) : (
            'Upload Image'
          )}
        </button>
      </div>
      <div className="mb-6">
        <h2 className="text-xl sm:text-2xl font-bold text-gray-900 mb-4">Designs Gallery</h2>
        <p className="text-gray-600 text-sm sm:text-base">
          Etsy store mockups and QNAP design files from your templates
        </p>
      </div>
      {/* Sub-tabs for Mockups and Design Files */}
      <div className="flex space-x-2 mb-6 overflow-x-auto">
        <button
          className={`tab-button whitespace-nowrap text-sm sm:text-base ${designsTab === 'mockups' ? 'active' : ''}`}
          onClick={() => setDesignsTab('mockups')}
        >
          Mockups
        </button>
        <button
          className={`tab-button whitespace-nowrap text-sm sm:text-base ${designsTab === 'designFiles' ? 'active' : ''}`}
          onClick={() => setDesignsTab('designFiles')}
        >
          Design Files
        </button>
      </div>
      {/* Mockups Tab */}
      {designsTab === 'mockups' && <MockupsGallery mockupImages={designs?.mockups || []} openImageModal={() => {}} />}
      {/* Design Files Tab */}
      {designsTab === 'designFiles' && (
        <DesignFilesGallery designFiles={designs?.files || []} openImageModal={() => {}} />
      )}

      {/* Template Selection Modal */}
      <DesignUploadModal
        isOpen={showDesignUploadModal}
        onClose={() => setShowDesignUploadModal(false)}
        onUpload={data => {
          setUploading(false);
          onRefresh();
        }}
      />

      {/* Back to Top Button */}
      <BackToTop />
    </div>
  );
};

export default DesignsTab;
