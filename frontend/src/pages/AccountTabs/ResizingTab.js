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
        api.get('/settings/canvas-config'),
        api.get('/settings/size-config')
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
      product_template_id: null,
      name: '',
      width_inches: 0,
      height_inches: 0,
      description: '',
      is_active: true,
      is_stretch: true
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
      await api.delete(`/settings/${editingCanvas.product_template_id}/canvas-config/${configId}`);
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
        await api.put(`/settings/${editingCanvas.product_template_id}/canvas-config/${editingCanvas.id}`, configData);
        setMessage('Canvas configuration updated successfully');
      } else {
        await api.post(`/settings/${configData.product_template_id}/canvas-config`, configData);
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
      product_template_id: null,
      canvas_id: null,
      name: '',
      width_inches: 0,
      height_inches: 0,
      description: '',
      is_active: true
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
      await api.delete(`/settings/${editingSize.product_template_id}/${editingSize.canvas_id}/size-config/${configId}`);
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
        await api.put(`/settings/${editingSize.product_template_id}/${editingSize.canvas_id}/size-config/${editingSize.id}`, configData);
        setMessage('Size configuration updated successfully');
      } else {
        await api.post(`/settings/${configData.product_template_id}/${configData.canvas_id}/size-config`, configData);
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
    product_template_id: config?.product_template_id || null,
    name: config?.name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    description: config?.description || '',
    is_active: config?.is_active !== undefined ? config.is_active : true,
    is_stretch: config?.is_stretch !== undefined ? config.is_stretch : true
  });
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [showTemplateSelector, setShowTemplateSelector] = useState(!config?.id);
  const api = useApi();

  useEffect(() => {
    const fetchTemplates = async () => {
      try {
        const response = await api.get('/settings/product-template');
        setTemplates(response);
      } catch (error) {
        console.error('Error fetching templates:', error);
        setTemplates([]);
      }
    };
    fetchTemplates();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.product_template_id) {
      alert('Please select a template');
      return;
    }
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

  const handleTemplateSelect = (template) => {
    setFormData(prev => ({ ...prev, product_template_id: template.id }));
    setShowTemplateSelector(false);
  };

  if (showTemplateSelector) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Select Template for Canvas Configuration
          </h3>
          
          {templates.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No templates found. Please create a template first.</p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    {template.name}
                  </h4>
                  {template.template_title && (
                    <p className="text-sm text-gray-600 mb-2">{template.template_title}</p>
                  )}
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Price: ${template.price || 0}</div>
                    <div>Type: {template.type || 'N/A'}</div>
                    <div>Quantity: {template.quantity || 0}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">
            {config?.id ? 'Edit Canvas Configuration' : 'Create Canvas Configuration'}
          </h3>
          <button
            onClick={() => setShowTemplateSelector(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Change Template
          </button>
        </div>
        
        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Selected Template:</strong> {templates.find(t => t.id === formData.product_template_id)?.name || 'Unknown'}
          </p>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Canvas Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
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

          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => handleInputChange('is_active', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Active</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_stretch}
                onChange={(e) => handleInputChange('is_stretch', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Stretch</span>
            </label>
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
    product_template_id: config?.product_template_id || null,
    canvas_id: config?.canvas_id || null,
    name: config?.name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    description: config?.description || '',
    is_active: config?.is_active !== undefined ? config.is_active : true
  });
  const [loading, setLoading] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [canvasConfigs, setCanvasConfigs] = useState([]);
  const [showTemplateSelector, setShowTemplateSelector] = useState(!config?.id);
  const [showCanvasSelector, setShowCanvasSelector] = useState(!config?.id && !config?.product_template_id);
  const api = useApi();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [templatesResponse, canvasResponse] = await Promise.all([
          api.get('/settings/product-template'),
          api.get('/settings/canvas-config')
        ]);
        setTemplates(templatesResponse);
        setCanvasConfigs(canvasResponse);
      } catch (error) {
        console.error('Error fetching data:', error);
        setTemplates([]);
        setCanvasConfigs([]);
      }
    };
    fetchData();
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!formData.product_template_id) {
      alert('Please select a template');
      return;
    }
    if (!formData.canvas_id) {
      alert('Please select a canvas configuration');
      return;
    }
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

  const handleTemplateSelect = (template) => {
    setFormData(prev => ({ 
      ...prev, 
      product_template_id: template.id,
      canvas_id: null // Reset canvas selection when template changes
    }));
    setShowTemplateSelector(false);
    setShowCanvasSelector(true);
  };

  const handleCanvasSelect = (canvas) => {
    setFormData(prev => ({ ...prev, canvas_id: canvas.id }));
    setShowCanvasSelector(false);
  };

  // Filter canvas configs for the selected template
  const filteredCanvasConfigs = canvasConfigs.filter(canvas => 
    canvas.product_template_id === formData.product_template_id
  );

  if (showTemplateSelector) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Select Template for Size Configuration
          </h3>
          
          {templates.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No templates found. Please create a template first.</p>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    {template.name}
                  </h4>
                  {template.template_title && (
                    <p className="text-sm text-gray-600 mb-2">{template.template_title}</p>
                  )}
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Price: ${template.price || 0}</div>
                    <div>Type: {template.type || 'N/A'}</div>
                    <div>Quantity: {template.quantity || 0}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
          
          <div className="flex justify-end mt-6">
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (showCanvasSelector) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">
            Select Canvas Configuration
          </h3>
          
          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Selected Template:</strong> {templates.find(t => t.id === formData.product_template_id)?.name || 'Unknown'}
            </p>
          </div>
          
          {filteredCanvasConfigs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No canvas configurations found for this template. Please create a canvas configuration first.</p>
              <button
                onClick={() => setShowTemplateSelector(true)}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors mr-2"
              >
                Back to Templates
              </button>
              <button
                onClick={onClose}
                className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600 transition-colors"
              >
                Close
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredCanvasConfigs.map((canvas) => (
                <div
                  key={canvas.id}
                  onClick={() => handleCanvasSelect(canvas)}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">
                    {canvas.name}
                  </h4>
                  <div className="text-xs text-gray-500 space-y-1">
                    <div>Width: {canvas.width_inches}"</div>
                    <div>Height: {canvas.height_inches}"</div>
                    <div>Active: {canvas.is_active ? 'Yes' : 'No'}</div>
                    <div>Stretch: {canvas.is_stretch ? 'Yes' : 'No'}</div>
                  </div>
                  {canvas.description && (
                    <p className="text-sm text-gray-600 mt-2">{canvas.description}</p>
                  )}
                </div>
              ))}
            </div>
          )}
          
          <div className="flex justify-end mt-6">
            <button
              onClick={() => setShowTemplateSelector(true)}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors mr-2"
            >
              Back to Templates
            </button>
            <button
              onClick={onClose}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4 max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-xl font-semibold text-gray-900">
            {config?.id ? 'Edit Size Configuration' : 'Create Size Configuration'}
          </h3>
          <button
            onClick={() => setShowTemplateSelector(true)}
            className="text-sm text-blue-600 hover:text-blue-800"
          >
            Change Selection
          </button>
        </div>
        
        <div className="mb-4 space-y-2">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Template:</strong> {templates.find(t => t.id === formData.product_template_id)?.name || 'Unknown'}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Canvas:</strong> {canvasConfigs.find(c => c.id === formData.canvas_id)?.name || 'Unknown'}
            </p>
          </div>
        </div>
        
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Size Name *
            </label>
            <input
              type="text"
              value={formData.name}
              onChange={(e) => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Adult+, Adult, Youth"
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

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={(e) => handleInputChange('is_active', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Active</span>
            </label>
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