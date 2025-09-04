import { useState, useEffect, useRef, Component } from 'react';
import { useApi } from '../hooks/useApi';

// Error Boundary Component
class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('EditMockupModal Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="p-4 bg-red-100 border border-red-300 rounded-lg">
          <h3 className="text-red-800 font-semibold">Something went wrong</h3>
          <p className="text-red-600 text-sm">Please close and reopen the modal</p>
        </div>
      );
    }

    return this.props.children;
  }
}

const EditMockupModal = ({ isOpen, onClose, mockup, onUpdate }) => {
  // All hooks must be called before any early returns
  const api = useApi();
  const fileInputRef = useRef(null);
  const [formData, setFormData] = useState({
    name: '',
    starting_name: 100
  });
  const [watermarkFile, setWatermarkFile] = useState(null);
  const [watermarkPreview, setWatermarkPreview] = useState(null);
  const [currentWatermarkPath, setCurrentWatermarkPath] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');
  
  // Early return after all hooks are defined
  if (!isOpen || !mockup) return null;

  useEffect(() => {
    if (mockup) {
      setFormData({
        name: mockup.name || '',
        starting_name: mockup.starting_name || 100
      });
      // Get current watermark path from the first mockup image
      try {
        if (mockup.mockup_images && mockup.mockup_images.length > 0) {
          const firstImageWatermark = mockup.mockup_images[0].watermark_path;
          setCurrentWatermarkPath(firstImageWatermark || '');
        }
      } catch (error) {
        console.error('Error setting watermark path:', error);
        setCurrentWatermarkPath('');
      }
    }
  }, [mockup]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      // Update basic mockup info
      await api.put(`/mockups/update/${mockup.id}`, {
        starting_name: formData.starting_name
      });

      // If a new watermark file is selected, update the watermark for all mockup images
      if (watermarkFile) {
        const watermarkFormData = new FormData();
        watermarkFormData.append('watermark', watermarkFile);
        
        await api.putFormData(`/mockups/${mockup.id}/update-watermark`, watermarkFormData);
        
        setMessage('Mockup and watermark updated successfully!');
      } else {
        setMessage('Mockup updated successfully!');
      }

      if (onUpdate) {
        onUpdate();
      }
      
      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Error updating mockup:', error);
      let errorMessage = 'Failed to update mockup';
      
      if (error.response) {
        // The request was made and the server responded with a status code
        errorMessage = error.response.data?.detail || error.response.data?.message || errorMessage;
      } else if (error.request) {
        // The request was made but no response was received
        errorMessage = 'Network error - please check your connection';
      } else {
        // Something happened in setting up the request
        errorMessage = error.message || errorMessage;
      }
      
      setMessage(errorMessage);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'starting_name' ? parseInt(value) || 100 : value
    }));
  };

  const handleWatermarkChange = (e) => {
    try {
      const file = e.target.files?.[0];
      if (file) {
        // Validate file type
        if (!file.type.startsWith('image/')) {
          setMessage('Please select a valid image file for the watermark');
          return;
        }
        
        // Validate file size (max 10MB)
        if (file.size > 10 * 1024 * 1024) {
          setMessage('Watermark file size must be less than 10MB');
          return;
        }
        
        setWatermarkFile(file);
        setMessage('');
        
        // Create preview URL
        const previewUrl = URL.createObjectURL(file);
        setWatermarkPreview(previewUrl);
      }
    } catch (error) {
      console.error('Error handling watermark file:', error);
      setMessage('Error processing the selected file');
    }
  };

  const clearWatermark = () => {
    try {
      setWatermarkFile(null);
      if (watermarkPreview) {
        URL.revokeObjectURL(watermarkPreview);
        setWatermarkPreview(null);
      }
      // Reset file input using ref
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Error clearing watermark:', error);
    }
  };

  // Cleanup preview URL on unmount
  useEffect(() => {
    return () => {
      try {
        if (watermarkPreview) {
          URL.revokeObjectURL(watermarkPreview);
        }
      } catch (error) {
        console.error('Error cleaning up preview URL:', error);
      }
    };
  }, [watermarkPreview]);

  return (
    <ErrorBoundary>
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Edit Mockup</h2>
            <button
              onClick={onClose}
              className="text-gray-400 hover:text-gray-600"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Mockup Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Mockup Information</h3>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Mockup Name
                </label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  placeholder="Enter mockup name"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">Note: Name changes may not be saved in the current version</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Starting Name
                </label>
                <input
                  type="number"
                  name="starting_name"
                  value={formData.starting_name}
                  onChange={handleInputChange}
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
                <p className="mt-1 text-xs text-gray-500">The starting number for this mockup series</p>
              </div>
            </div>

            {/* Watermark Section */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Watermark Settings</h3>
              
              {/* Current Watermark Display */}
              {currentWatermarkPath && (
                <div className="bg-gray-50 p-4 rounded-lg">
                  <p className="text-sm text-gray-600 mb-2">Current Watermark:</p>
                  <p className="text-sm font-medium text-gray-800 truncate">{currentWatermarkPath}</p>
                </div>
              )}
              
              {/* New Watermark Upload */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Upload New Watermark (Optional)
                </label>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept="image/*"
                  onChange={handleWatermarkChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-medium file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
                />
                <p className="mt-1 text-xs text-gray-500">
                  Select a new watermark image to replace the current one. Supports PNG, JPG, and other image formats. Max size: 10MB.
                </p>
                
                {/* Watermark Preview */}
                {watermarkFile && (
                  <div className="mt-3 space-y-3">
                    <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                      <div className="flex items-center space-x-3">
                        {watermarkPreview && (
                          <img
                            src={watermarkPreview}
                            alt="Watermark preview"
                            className="w-12 h-12 object-contain rounded border border-gray-300"
                          />
                        )}
                        <div>
                          <p className="text-sm font-medium text-green-700">
                            New watermark selected
                          </p>
                          <p className="text-xs text-green-600 truncate max-w-xs">
                            {watermarkFile.name}
                          </p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={clearWatermark}
                        className="ml-3 text-red-500 hover:text-red-700 transition-colors"
                        title="Remove selected watermark"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                      </button>
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Read-only Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Information</h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Template:</span>
                  <span className="font-medium">{mockup.template_name || `Template ${mockup.product_template_id}` || 'N/A'}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Images:</span>
                  <span className="font-medium">{mockup.mockup_images?.length || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Masks:</span>
                  <span className="font-medium">
                    {mockup.mockup_images?.reduce((total, image) => 
                      total + (image.mask_data?.length || 0), 0) || 0}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Created:</span>
                  <span className="font-medium">{new Date(mockup.created_at).toLocaleDateString()}</span>
                </div>
              </div>
            </div>

            {/* Message */}
            {message && (
              <div className={`p-4 rounded-lg ${
                message.includes('successfully') 
                  ? 'bg-green-100 text-green-700' 
                  : 'bg-red-100 text-red-700'
              }`}>
                {message}
              </div>
            )}

            {/* Actions */}
            <div className="flex justify-end space-x-4 pt-4">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={loading}
                className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                  loading
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {loading ? 'Updating...' : 'Update Mockup'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
    </ErrorBoundary>
  );
};

export default EditMockupModal; 