import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const EditMockupModal = ({ isOpen, onClose, mockup, onUpdate }) => {
  const api = useApi();
  const [formData, setFormData] = useState({
    name: '',
    starting_name: 100,
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    if (mockup) {
      setFormData({
        name: mockup.name || '',
        starting_name: mockup.starting_name || 100,
      });
    }
  }, [mockup]);

  if (!isOpen || !mockup) return null;

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setMessage('');

    try {
      await api.put(`/mockups/update/${mockup.id}`, {
        starting_name: formData.starting_name,
      });

      setMessage('Mockup updated successfully!');
      if (onUpdate) {
        onUpdate();
      }

      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Error updating mockup:', error);
      setMessage('Failed to update mockup');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'starting_name' ? parseInt(value) || 100 : value,
    }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Edit Mockup</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Mockup Name</label>
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
                <label className="block text-sm font-medium text-gray-700 mb-2">Starting Name</label>
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

            {/* Read-only Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Current Information</h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-2">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Template:</span>
                  <span className="font-medium">
                    {mockup.template_name || `Template ${mockup.product_template_id}` || 'N/A'}
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Images:</span>
                  <span className="font-medium">{mockup.mockup_images?.length || 0}</span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Total Masks:</span>
                  <span className="font-medium">
                    {mockup.mockup_images?.reduce((total, image) => total + (image.mask_data?.length || 0), 0) || 0}
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
              <div
                className={`p-4 rounded-lg ${
                  message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                }`}
              >
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
                  loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {loading ? 'Updating...' : 'Update Mockup'}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
};

export default EditMockupModal;
