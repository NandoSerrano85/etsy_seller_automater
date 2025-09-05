import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';

// Templates Tab Component
const TemplatesTab = () => {
  const api = useApi();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings/product-template');
      setTemplates(response);
      setMessage('');
    } catch (error) {
      console.error('Error fetching templates:', error);
      setMessage('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setEditingTemplate({
      name: '',
      template_title: '',
      title: '',
      description: '',
      who_made: 'i_did',
      when_made: 'made_to_order',
      taxonomy_id: 1,
      price: 0.0,
      materials: [],
      shop_section_id: 2,
      quantity: 100,
      tags: [],
      item_weight: 2.5,
      item_weight_unit: 'oz',
      item_length: 11,
      item_width: 9.5,
      item_height: 1,
      item_dimensions_unit: 'in',
      is_taxable: true,
      type: 'physical',
      processing_min: 1,
      processing_max: 3,
      return_policy_id: null,
    });
    setShowEditModal(true);
  };

  const handleEditTemplate = template => {
    setEditingTemplate({
      ...template,
      materials: template.materials ? template.materials.split(',') : [],
      tags: template.tags ? template.tags.split(',') : [],
    });
    setShowEditModal(true);
  };

  const handleDeleteTemplate = async templateId => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      await api.delete(`/settings/product-template/${templateId}`);
      setMessage('Template deleted successfully');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      setMessage('Failed to delete template');
    }
  };

  const handleSaveTemplate = async templateData => {
    try {
      if (editingTemplate.id) {
        // Update existing template
        await api.put(`/settings/product-template/${editingTemplate.id}`, templateData);
        setMessage('Template updated successfully');
      } else {
        // Create new template
        await api.post('/settings/product-template', templateData);
        setMessage('Template created successfully');
      }
      setShowEditModal(false);
      setEditingTemplate(null);
      fetchTemplates();
    } catch (error) {
      console.error('Error saving template:', error);
      setMessage(error.message || 'Failed to save template');
    }
  };

  const handleCreateDefaultTemplate = async () => {
    try {
      await api.post('/settings/product-template/default');
      setMessage('Default template created successfully');
      fetchTemplates();
    } catch (error) {
      console.error('Error creating default template:', error);
      setMessage(error.message || 'Failed to create default template');
    }
  };

  return (
    <div className="space-y-8 mt-0">
      <div className="card p-8">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-3xl font-bold text-gray-900">Product Templates</h2>
          <div className="flex space-x-4">
            <button
              onClick={handleCreateDefaultTemplate}
              className="px-4 py-2 bg-yellow-500 text-white rounded-lg hover:bg-yellow-600 transition-colors font-medium"
            >
              Create Default
            </button>
            <button
              onClick={handleCreateTemplate}
              className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
            >
              Add Template
            </button>
          </div>
        </div>

        {message && (
          <div
            className={`p-4 rounded-lg mb-6 ${
              message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {message}
          </div>
        )}

        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading templates...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {templates.length === 0 ? (
              <div className="col-span-full text-center py-12">
                <div className="text-gray-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">No templates found</h3>
                <p className="text-gray-600 mb-4">Create your first template to get started with your Etsy listings.</p>
                <button
                  onClick={handleCreateTemplate}
                  className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                >
                  Create Template
                </button>
              </div>
            ) : (
              templates.map(template => (
                <div
                  key={template.id}
                  className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
                >
                  <div className="flex justify-between items-start mb-4">
                    <h3 className="text-lg font-semibold text-gray-900">{template.template_title || template.name}</h3>
                    <span className="text-sm text-gray-500">#{template.id}</span>
                  </div>

                  <p className="text-sm text-gray-600 mb-4 line-clamp-2">{template.title || 'No listing title set'}</p>

                  {template.template_title && <p className="text-xs text-gray-500 mb-2">Key: {template.name}</p>}

                  <div className="space-y-2 mb-4">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Price:</span>
                      <span className="font-medium">${template.price || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Quantity:</span>
                      <span className="font-medium">{template.quantity || 0}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-500">Type:</span>
                      <span className="font-medium capitalize">{template.type || 'N/A'}</span>
                    </div>
                  </div>

                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleEditTemplate(template)}
                      className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                    >
                      Edit
                    </button>
                    <button
                      onClick={() => handleDeleteTemplate(template.id)}
                      className="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                    >
                      Delete
                    </button>
                  </div>
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Template Edit Modal */}
      {showEditModal && (
        <TemplateEditModal
          template={editingTemplate}
          onSave={handleSaveTemplate}
          onClose={() => {
            setShowEditModal(false);
            setEditingTemplate(null);
          }}
        />
      )}
    </div>
  );
};

// Template Edit Modal Component
const TemplateEditModal = ({ template, onSave, onClose }) => {
  const [formData, setFormData] = useState(template);
  const [loading, setLoading] = useState(false);
  const [taxonomies, setTaxonomies] = useState([]);
  const [shopSections, setShopSections] = useState([]);
  const api = useApi();

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [taxonomiesData, shopSectionsData] = await Promise.all([
          api.get('/settings/product-template/taxonomies'),
          api.get('/settings/product-template/shop-sections'),
        ]);
        setTaxonomies(taxonomiesData);
        setShopSections(shopSectionsData);
      } catch (err) {
        setTaxonomies([]);
        setShopSections([]);
      }
    };
    fetchData();
  }, []);

  const handleSubmit = async e => {
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

  const handleArrayChange = (field, value) => {
    const array = value
      .split(',')
      .map(item => item.trim())
      .filter(item => item);
    setFormData(prev => ({ ...prev, [field]: array }));
  };

  const handleArrayInputChange = (field, value) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleArrayKeyPress = (field, e) => {
    if (e.key === 'Enter' || e.key === ',') {
      e.preventDefault();
      const value = e.target.value.trim();
      if (value) {
        const currentArray = formData[field] || [];
        const maxItems = 13;

        if (!currentArray.includes(value) && currentArray.length < maxItems) {
          setFormData(prev => ({
            ...prev,
            [field]: [...currentArray, value],
          }));
        }
        e.target.value = '';
      }
    }
  };

  const removeArrayItem = (field, index) => {
    const newArray = formData[field].filter((_, i) => i !== index);
    setFormData(prev => ({ ...prev, [field]: newArray }));
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 !mt-0">
      <div className="bg-white rounded-lg p-6 w-full max-w-4xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">{template.id ? 'Edit Template' : 'Create Template'}</h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Basic Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Basic Information</h3>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
                <input
                  type="text"
                  value={formData.name || ''}
                  onChange={e => handleInputChange('name', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  required
                  placeholder="e.g., UVDTF 16oz"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Title</label>
                <input
                  type="text"
                  value={formData.template_title || ''}
                  onChange={e => handleInputChange('template_title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="e.g., My Custom Template Name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Listing Title Postfix</label>
                <input
                  type="text"
                  value={formData.title || ''}
                  onChange={e => handleInputChange('title', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Etsy listing title"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={formData.description || ''}
                  onChange={e => handleInputChange('description', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Who Made</label>
                <select
                  value={formData.who_made || 'i_did'}
                  onChange={e => handleInputChange('who_made', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="i_did">I did</option>
                  <option value="collective">A member of my shop</option>
                  <option value="someone_else">Another company or person</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">When Made</label>
                <select
                  value={formData.when_made || 'made_to_order'}
                  onChange={e => handleInputChange('when_made', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="made_to_order">Made to order</option>
                  <option value="2020_2025">2020-2025</option>
                  <option value="2010_2019">2010-2019</option>
                  <option value="2006_2009">2006-2009</option>
                  <option value="before_2006">Before 2006</option>
                  <option value="2000_2005">2000-2005</option>
                  <option value="1990s">1990s</option>
                  <option value="1980s">1980s</option>
                  <option value="1970s">1970s</option>
                  <option value="1960s">1960s</option>
                  <option value="1950s">1950s</option>
                  <option value="1940s">1940s</option>
                  <option value="1930s">1930s</option>
                  <option value="1920s">1920s</option>
                  <option value="1910s">1910s</option>
                  <option value="1900s">1900s</option>
                  <option value="1800s">1800s</option>
                  <option value="1700s">1700s</option>
                  <option value="before_1700">Before 1700</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Type</label>
                <select
                  value={formData.type || 'physical'}
                  onChange={e => handleInputChange('type', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="physical">Physical</option>
                  <option value="digital">Digital</option>
                </select>
              </div>
            </div>

            {/* Pricing & Inventory */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Pricing & Inventory</h3>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Price ($)</label>
                <input
                  type="number"
                  min="0"
                  step="0.01"
                  placeholder="0.00"
                  value={formData.price || ''}
                  onChange={e => {
                    const value = parseFloat(e.target.value);
                    if (!isNaN(value) && value >= 0) {
                      // Limit to 2 decimal places
                      const roundedValue = Math.round(value * 100) / 100;
                      handleInputChange('price', roundedValue);
                    } else if (e.target.value === '') {
                      handleInputChange('price', null);
                    }
                  }}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Quantity</label>
                <input
                  type="number"
                  value={formData.quantity || ''}
                  onChange={e => handleInputChange('quantity', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Materials</label>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-500">
                    {formData.materials ? formData.materials.length : 0}/13 materials
                  </span>
                  {formData.materials && formData.materials.length >= 13 && (
                    <span className="text-xs text-red-500">Maximum reached</span>
                  )}
                </div>
                <input
                  type="text"
                  placeholder={
                    formData.materials && formData.materials.length >= 13
                      ? 'Maximum materials reached'
                      : 'Type materials and press Enter or comma to add'
                  }
                  onChange={e => handleArrayChange('materials', e.target.value)}
                  onKeyPress={e => handleArrayKeyPress('materials', e)}
                  disabled={formData.materials && formData.materials.length >= 13}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formData.materials && formData.materials.length >= 13 ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                />
                {formData.materials && formData.materials.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.materials.map((material, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                      >
                        {material}
                        <button
                          type="button"
                          onClick={() => removeArrayItem('materials', index)}
                          className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-blue-400 hover:bg-blue-200 hover:text-blue-500 focus:outline-none"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
                <div className="flex justify-between items-center mb-1">
                  <span className="text-xs text-gray-500">{formData.tags ? formData.tags.length : 0}/13 tags</span>
                  {formData.tags && formData.tags.length >= 13 && (
                    <span className="text-xs text-red-500">Maximum reached</span>
                  )}
                </div>
                <input
                  type="text"
                  placeholder={
                    formData.tags && formData.tags.length >= 13
                      ? 'Maximum tags reached'
                      : 'Type tags and press Enter or comma to add'
                  }
                  onChange={e => handleArrayChange('tags', e.target.value)}
                  onKeyPress={e => handleArrayKeyPress('tags', e)}
                  disabled={formData.tags && formData.tags.length >= 13}
                  className={`w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 ${
                    formData.tags && formData.tags.length >= 13 ? 'bg-gray-100 cursor-not-allowed' : ''
                  }`}
                />
                {formData.tags && formData.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-2">
                    {formData.tags.map((tag, index) => (
                      <span
                        key={index}
                        className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800"
                      >
                        {tag}
                        <button
                          type="button"
                          onClick={() => removeArrayItem('tags', index)}
                          className="ml-1.5 inline-flex items-center justify-center w-4 h-4 rounded-full text-green-400 hover:bg-green-200 hover:text-green-500 focus:outline-none"
                        >
                          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </button>
                      </span>
                    ))}
                  </div>
                )}
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Is Taxable</label>
                <select
                  value={formData.is_taxable ? 'true' : 'false'}
                  onChange={e => handleInputChange('is_taxable', e.target.value === 'true')}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="true">Yes</option>
                  <option value="false">No</option>
                </select>
              </div>
            </div>
          </div>

          {/* Additional Fields */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Etsy Specific */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">Etsy Settings</h3>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Taxonomy</label>
                <select
                  value={formData.taxonomy_id || ''}
                  onChange={e => handleInputChange('taxonomy_id', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a category</option>
                  {taxonomies.map(tax => (
                    <option key={tax.id} value={tax.id}>
                      {tax.name} (ID: {tax.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Shop Section</label>
                <select
                  value={formData.shop_section_id || ''}
                  onChange={e => handleInputChange('shop_section_id', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="">Select a shop section</option>
                  {shopSections.map(section => (
                    <option key={section.id} value={section.id}>
                      {section.name} (ID: {section.id})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Return Policy</label>
                <select
                  value={formData.return_policy_id === 1 ? 'yes' : 'no'}
                  onChange={e => handleInputChange('return_policy_id', e.target.value === 'yes' ? 1 : null)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value="no">No</option>
                  <option value="yes">Yes</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Processing Min (days)</label>
                <input
                  type="number"
                  value={formData.processing_min || ''}
                  onChange={e => handleInputChange('processing_min', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Processing Max (days)</label>
                <input
                  type="number"
                  value={formData.processing_max || ''}
                  onChange={e => handleInputChange('processing_max', parseInt(e.target.value))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            {/* Physical Dimensions */}
            {formData.type === 'physical' && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold text-gray-900">Physical Dimensions</h3>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Item Weight</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.item_weight || ''}
                    onChange={e => handleInputChange('item_weight', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Weight Unit</label>
                  <select
                    value={formData.item_weight_unit || 'oz'}
                    onChange={e => handleInputChange('item_weight_unit', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="oz">Ounces</option>
                    <option value="lb">Pounds</option>
                    <option value="g">Grams</option>
                    <option value="kg">Kilograms</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Length</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.item_length || ''}
                    onChange={e => handleInputChange('item_length', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Width</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.item_width || ''}
                    onChange={e => handleInputChange('item_width', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Height</label>
                  <input
                    type="number"
                    step="0.01"
                    value={formData.item_height || ''}
                    onChange={e => handleInputChange('item_height', parseFloat(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Dimensions Unit</label>
                  <select
                    value={formData.item_dimensions_unit || 'in'}
                    onChange={e => handleInputChange('item_dimensions_unit', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="in">Inches</option>
                    <option value="cm">Centimeters</option>
                    <option value="mm">Millimeters</option>
                    <option value="ft">Feet</option>
                  </select>
                </div>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          <div className="flex justify-end space-x-4 pt-6 border-t">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {loading ? 'Saving...' : template.id ? 'Update Template' : 'Create Template'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TemplatesTab;
