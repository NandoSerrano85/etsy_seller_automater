import React from 'react';

const ViewMockupModal = ({ isOpen, onClose, mockup }) => {
  if (!isOpen || !mockup) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">View Mockup Details</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-500">Mockup Name</label>
                  <p className="mt-1 text-sm text-gray-900">{mockup.name || `Mockup #${mockup.id.slice(0, 8)}`}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Template</label>
                  <p className="mt-1 text-sm text-gray-900">
                    {mockup.template_name || `Template ${mockup.product_template_id}` || 'N/A'}
                  </p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Starting Name</label>
                  <p className="mt-1 text-sm text-gray-900">{mockup.starting_name}</p>
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-500">Created</label>
                  <p className="mt-1 text-sm text-gray-900">{new Date(mockup.created_at).toLocaleDateString()}</p>
                </div>
              </div>
            </div>

            {/* Statistics */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Statistics</h3>
              <div className="grid grid-cols-2 gap-4">
                <div className="bg-blue-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600">{mockup.mockup_images?.length || 0}</div>
                  <div className="text-sm text-blue-600">Total Images</div>
                </div>
                <div className="bg-green-50 p-4 rounded-lg">
                  <div className="text-2xl font-bold text-green-600">
                    {mockup.mockup_images?.reduce((total, image) => total + (image.mask_data?.length || 0), 0) || 0}
                  </div>
                  <div className="text-sm text-green-600">Total Masks</div>
                </div>
              </div>
            </div>
          </div>

          {/* Images Section */}
          {mockup.mockup_images && mockup.mockup_images.length > 0 && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Mockup Images</h3>
              <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                {mockup.mockup_images.map((image, index) => (
                  <div key={image.id} className="border rounded-lg p-3">
                    <div className="aspect-square bg-gray-100 rounded-lg mb-2 flex items-center justify-center">
                      <span className="text-gray-500 text-sm">
                        <img src={`file:///${image.file_path}`} alt={`Mockup image ${index + 1}`} />
                      </span>
                    </div>
                    <div className="text-xs text-gray-600">
                      <div>Filename: {image.filename}</div>
                      <div>Masks: {image.mask_data?.length || 0}</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mask Data Summary */}
          {mockup.mockup_images && mockup.mockup_images.some(img => img.mask_data && img.mask_data.length > 0) && (
            <div className="mt-8">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Mask Data Summary</h3>
              <div className="bg-gray-50 rounded-lg p-4">
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {mockup.mockup_images.map(
                    (image, index) =>
                      image.mask_data &&
                      image.mask_data.length > 0 && (
                        <div key={image.id} className="bg-white p-3 rounded border">
                          <h4 className="font-medium text-sm text-gray-900 mb-2">Image {index + 1}</h4>
                          <div className="space-y-1 text-xs text-gray-600">
                            {image.mask_data.map((mask, maskIndex) => (
                              <div key={mask.id} className="flex justify-between">
                                <span>Mask {maskIndex + 1}:</span>
                                <span>{mask.points?.length || 0} points</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )
                  )}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default ViewMockupModal;
