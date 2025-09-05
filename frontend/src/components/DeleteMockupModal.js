import React, { useState } from 'react';
import { useApi } from '../hooks/useApi';

const DeleteMockupModal = ({ isOpen, onClose, mockup, onDelete }) => {
  const api = useApi();
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  if (!isOpen || !mockup) return null;

  const handleDelete = async () => {
    setLoading(true);
    setMessage('');

    try {
      await api.delete(`/mockups/delete/${mockup.id}`);

      setMessage('Mockup deleted successfully!');
      if (onDelete) {
        onDelete();
      }

      // Close modal after a short delay
      setTimeout(() => {
        onClose();
      }, 1500);
    } catch (error) {
      console.error('Error deleting mockup:', error);
      setMessage('Failed to delete mockup');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-md w-full">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-lg font-medium text-gray-900">Delete Mockup</h3>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-6">
          <div className="mb-4">
            <p className="text-sm text-gray-500">
              Are you sure you want to delete this mockup? This action cannot be undone.
            </p>
          </div>

          {/* Mockup Details */}
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
            <h4 className="font-medium text-red-800 mb-2">Mockup to be deleted:</h4>
            <div className="space-y-1 text-sm text-red-700">
              <div>
                <strong>Name:</strong> {mockup.name || `Mockup #${mockup.id.slice(0, 8)}`}
              </div>
              <div>
                <strong>Template:</strong> {mockup.template_name || `Template ${mockup.product_template_id}` || 'N/A'}
              </div>
              <div>
                <strong>Images:</strong> {mockup.mockup_images?.length || 0}
              </div>
              <div>
                <strong>Total Masks:</strong>{' '}
                {mockup.mockup_images?.reduce((total, image) => total + (image.mask_data?.length || 0), 0) || 0}
              </div>
            </div>
          </div>

          {/* Warning */}
          <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
            <div className="flex">
              <div className="flex-shrink-0">
                <svg className="h-5 w-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L3.732 16.5c-.77.833.192 2.5 1.732 2.5z"
                  />
                </svg>
              </div>
              <div className="ml-3">
                <h3 className="text-sm font-medium text-yellow-800">Warning</h3>
                <div className="mt-2 text-sm text-yellow-700">
                  <p>This will permanently delete:</p>
                  <ul className="list-disc list-inside mt-1">
                    <li>All mockup images</li>
                    <li>All mask data</li>
                    <li>All associated files</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>

          {/* Message */}
          {message && (
            <div
              className={`p-4 rounded-lg mb-4 ${
                message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
              }`}
            >
              {message}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end space-x-3">
            <button
              type="button"
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors disabled:opacity-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleDelete}
              disabled={loading}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-red-600 text-white hover:bg-red-700'
              }`}
            >
              {loading ? 'Deleting...' : 'Delete Mockup'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default DeleteMockupModal;
