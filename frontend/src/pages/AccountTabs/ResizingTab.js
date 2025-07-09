import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';

// Resizing Tab Component
const ResizingTab = () => {
  const api = useApi();
  const [canvasConfigs, setCanvasConfigs] = useState([]);
  const [sizeConfigs, setSizeConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('canvas'); // 'canvas' or 'size'
  const [showCanvasModal, setShowCanvasModal] = useState(false);
  const [showSizeModal, setShowSizeModal] = useState(false);
  const [editingCanvas, setEditingCanvas] = useState(null);
  const [editingSize, setEditingSize] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchConfigurations();
  }, []);

  const fetchConfigurations = async () => {
    try {
      setLoading(true);
      const [canvasResponse, sizeResponse] = await Promise.all([
        api.get('/api/canvas-configs'),
        api.get('/api/size-configs')
      ]);
      setCanvasConfigs(canvasResponse);
      setSizeConfigs(sizeResponse);
      setMessage('');
    } catch (error) {
      console.error('Error fetching configurations:', error);
      setMessage('Failed to load configurations');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateCanvas = () => {
    setEditingCanvas({
      template_name: '',
      width_inches: 0,
      height_inches: 0,
      description: ''
    });
    setShowCanvasModal(true);
  };

  const handleEditCanvas = (config) => {
    setEditingCanvas({ ...config });
    setShowCanvasModal(true);
  };

  const handleDeleteCanvas = async (configId) => {
    if (!window.confirm('Are you sure you want to delete this canvas configuration?')) {
      return;
    }

    try {
      await api.delete(`/api/canvas-configs/${configId}`);
      setMessage('Canvas configuration deleted successfully');
      fetchConfigurations();
    } catch (error) {
      console.error('Error deleting canvas config:', error);
      setMessage('Failed to delete canvas configuration');
    }
  };

  const handleSaveCanvas = async (configData) => {
    try {
      if (editingCanvas.id) {
        await api.put(`/api/canvas-configs/${editingCanvas.id}`, configData);
        setMessage('Canvas configuration updated successfully');
      } else {
        await api.post('/api/canvas-configs', configData);
        setMessage('Canvas configuration created successfully');
      }
      setShowCanvasModal(false);
      setEditingCanvas(null);
      fetchConfigurations();
    } catch (error) {
      console.error('Error saving canvas config:', error);
      setMessage(error.message || 'Failed to save canvas configuration');
    }
  };

  const handleCreateSize = () => {
    setEditingSize({
      template_name: '',
      size_name: '',
      width_inches: 0,
      height_inches: 0,
      description: ''
    });
    setShowSizeModal(true);
  };

  const handleEditSize = (config) => {
    setEditingSize({ ...config });
    setShowSizeModal(true);
  };

  const handleDeleteSize = async (configId) => {
    if (!window.confirm('Are you sure you want to delete this size configuration?')) {
      return;
    }

    try {
      await api.delete(`/api/size-configs/${configId}`);
      setMessage('Size configuration deleted successfully');
      fetchConfigurations();
    } catch (error) {
      console.error('Error deleting size config:', error);
      setMessage('Failed to delete size configuration');
    }
  };

  const handleSaveSize = async (configData) => {
    try {
      if (editingSize.id) {
        await api.put(`/api/size-configs/${editingSize.id}`, configData);
        setMessage('Size configuration updated successfully');
      } else {
        await api.post('/api/size-configs', configData);
        setMessage('Size configuration created successfully');
      }
      setShowSizeModal(false);
      setEditingSize(null);
      fetchConfigurations();
    } catch (error) {
      console.error('Error saving size config:', error);
      setMessage(error.message || 'Failed to save size configuration');
    }
  };

  return (
    <div className="space-y-8 mt-0">
      <div className="card p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Resizing Configurations</h2>
          <div className="flex space-x-4">
            <button
              onClick={() => setActiveSection('canvas')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeSection === 'canvas'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Canvas Configs
            </button>
            <button
              onClick={() => setActiveSection('size')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                activeSection === 'size'
                  ? 'bg-blue-500 text-white'
                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
              }`}
            >
              Size Configs
            </button>
          </div>
        </div>

        {message && (
          <div className={`p-4 rounded-lg mb-6 ${
            message.includes('successfully') 
              ? 'bg-green-100 text-green-700' 
              : 'bg-red-100 text-red-700'
          }`}>
            {message}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading configurations...</p>
          </div>
        ) : (
          <>
            {/* Canvas Configurations Section */}
            {activeSection === 'canvas' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">Canvas Configurations</h3>
                  <button
                    onClick={handleCreateCanvas}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
                  >
                    Add Canvas Config
                  </button>
                </div>

                {canvasConfigs.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No canvas configurations found</h3>
                    <p className="text-gray-600 mb-4">Create your first canvas configuration to define canvas dimensions for your templates.</p>
                    <button
                      onClick={handleCreateCanvas}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Create Canvas Config
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {canvasConfigs.map((config) => (
                      <div key={config.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-4">
                          <h4 className="text-lg font-semibold text-gray-900">
                            {config.template_name}
                          </h4>
                          <span className="text-sm text-gray-500">#{config.id}</span>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">Width:</span>
                            <span className="font-medium">{config.width_inches}"</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">Height:</span>
                            <span className="font-medium">{config.height_inches}"</span>
                          </div>
                          {config.description && (
                            <div className="text-sm text-gray-600 mt-2">
                              {config.description}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditCanvas(config)}
                            className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteCanvas(config.id)}
                            className="flex-1 px-3 py-2 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Size Configurations Section */}
            {activeSection === 'size' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-900">Size Configurations</h3>
                  <button
                    onClick={handleCreateSize}
                    className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
                  >
                    Add Size Config
                  </button>
                </div>

                {sizeConfigs.length === 0 ? (
                  <div className="text-center py-12">
                    <div className="text-gray-400 mb-4">
                      <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">No size configurations found</h3>
                    <p className="text-gray-600 mb-4">Create your first size configuration to define dimensions for your templates.</p>
                    <button
                      onClick={handleCreateSize}
                      className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Create Size Config
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {sizeConfigs.map((config) => (
                      <div key={config.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
                        <div className="flex justify-between items-start mb-4">
                          <h4 className="text-lg font-semibold text-gray-900">
                            {config.template_name}
                            {config.size_name && (
                              <span className="text-sm text-gray-500 ml-2">({config.size_name})</span>
                            )}
                          </h4>
                          <span className="text-sm text-gray-500">#{config.id}</span>
                        </div>
                        
                        <div className="space-y-2 mb-4">
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">Width:</span>
                            <span className="font-medium">{config.width_inches}"</span>
                          </div>
                          <div className="flex justify-between text-sm">
                            <span className="text-gray-500">Height:</span>
                            <span className="font-medium">{config.height_inches}"</span>
                          </div>
                          {config.description && (
                            <div className="text-sm text-gray-600 mt-2">
                              {config.description}
                            </div>
                          )}
                        </div>
                        
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleEditSize(config)}
                            className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteSize(config.id)}
                            className="flex-1 px-3 py-2 bg-red-500 text-white text-sm rounded hover:bg-red-600 transition-colors"
                          >
                            Delete
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </>
        )}
      </div>

      {/* Canvas Configuration Modal */}
      {showCanvasModal && (
        <CanvasConfigModal
          config={editingCanvas}
          onSave={handleSaveCanvas}
          onClose={() => {
            setShowCanvasModal(false);
            setEditingCanvas(null);
          }}
        />
      )}

      {/* Size Configuration Modal */}
      {showSizeModal && (
        <SizeConfigModal
          config={editingSize}
          onSave={handleSaveSize}
          onClose={() => {
            setShowSizeModal(false);
            setEditingSize(null);
          }}
        />
      )}
    </div>
  );
};

// Canvas Configuration Modal Component
const CanvasConfigModal = ({ config, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    template_name: config?.template_name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    description: config?.description || ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave(formData);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">
          {config?.id ? 'Edit Canvas Configuration' : 'Create Canvas Configuration'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name *
            </label>
            <input
              type="text"
              value={formData.template_name}
              onChange={(e) => handleInputChange('template_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., UVDTF Decal"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Width (inches) *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.width_inches}
              onChange={(e) => handleInputChange('width_inches', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="4.0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Height (inches) *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.height_inches}
              onChange={(e) => handleInputChange('height_inches', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="4.0"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional description"
              rows="3"
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                loading 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {loading ? 'Saving...' : (config?.id ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// Size Configuration Modal Component
const SizeConfigModal = ({ config, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    template_name: config?.template_name || '',
    size_name: config?.size_name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    description: config?.description || ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    try {
      await onSave(formData);
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">
          {config?.id ? 'Edit Size Configuration' : 'Create Size Configuration'}
        </h3>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Template Name *
            </label>
            <input
              type="text"
              value={formData.template_name}
              onChange={(e) => handleInputChange('template_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., UVDTF 16oz"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Size Name
            </label>
            <input
              type="text"
              value={formData.size_name}
              onChange={(e) => handleInputChange('size_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Adult+, Adult, Youth (optional)"
            />
            <p className="text-xs text-gray-500 mt-1">Leave empty for templates without size variants</p>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Width (inches) *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.width_inches}
              onChange={(e) => handleInputChange('width_inches', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="9.5"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Height (inches) *
            </label>
            <input
              type="number"
              step="0.01"
              value={formData.height_inches}
              onChange={(e) => handleInputChange('height_inches', parseFloat(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="4.33"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={formData.description}
              onChange={(e) => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Optional description"
              rows="3"
            />
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={onClose}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                loading 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {loading ? 'Saving...' : (config?.id ? 'Update' : 'Create')}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default ResizingTab; 