import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';

// Templates Tab Component
const TemplatesTab = () => {
  const api = useApi();
  const [etsyTemplates, setEtsyTemplates] = useState([]);
  const [shopifyTemplates, setShopifyTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTypeSelectionModal, setShowTypeSelectionModal] = useState(false);
  const [editingTemplate, setEditingTemplate] = useState(null);
  const [selectedTemplateType, setSelectedTemplateType] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchTemplates();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const [etsyResponse, shopifyResponse] = await Promise.all([
        api.get('/settings/product-template'),
        api.get('/settings/shopify-product-template'),
      ]);
      setEtsyTemplates(etsyResponse);
      setShopifyTemplates(shopifyResponse);
      setMessage('');
    } catch (error) {
      console.error('Error fetching templates:', error);
      setMessage('Failed to load templates');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateTemplate = () => {
    setShowTypeSelectionModal(true);
  };

  const handleTemplateTypeSelected = type => {
    setSelectedTemplateType(type);
    setShowTypeSelectionModal(false);

    if (type === 'etsy') {
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
    } else {
      // Shopify template defaults
      setEditingTemplate({
        name: '',
        template_title: '',
        description: '',
        vendor: '',
        product_type: '',
        tags: [],
        price: 0.0,
        compare_at_price: null,
        cost_per_item: null,
        sku_prefix: '',
        barcode_prefix: '',
        track_inventory: true,
        inventory_quantity: 0,
        inventory_policy: 'deny',
        fulfillment_service: 'manual',
        requires_shipping: true,
        weight: null,
        weight_unit: 'g',
        has_variants: false,
        option1_name: '',
        option1_values: [],
        option2_name: '',
        option2_values: [],
        option3_name: '',
        option3_values: [],
        status: 'draft',
        published_scope: 'web',
        seo_title: '',
        seo_description: '',
        is_taxable: true,
        tax_code: '',
        gift_card: false,
        template_suffix: '',
      });
    }
    setShowEditModal(true);
  };

  const handleEditTemplate = (template, type) => {
    setSelectedTemplateType(type);
    if (type === 'etsy') {
      setEditingTemplate({
        ...template,
        materials: template.materials ? template.materials.split(',') : [],
        tags: template.tags ? template.tags.split(',') : [],
      });
    } else {
      setEditingTemplate({
        ...template,
        tags: template.tags ? template.tags.split(',') : [],
        option1_values: template.option1_values ? template.option1_values.split(',') : [],
        option2_values: template.option2_values ? template.option2_values.split(',') : [],
        option3_values: template.option3_values ? template.option3_values.split(',') : [],
      });
    }
    setShowEditModal(true);
  };

  const handleDeleteTemplate = async (templateId, type) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      const endpoint = type === 'etsy' ? 'product-template' : 'shopify-product-template';
      await api.delete(`/settings/${endpoint}/${templateId}`);
      setMessage('Template deleted successfully');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      setMessage('Failed to delete template');
    }
  };

  const handleSaveTemplate = async templateData => {
    try {
      const endpoint = selectedTemplateType === 'etsy' ? 'product-template' : 'shopify-product-template';

      if (editingTemplate.id) {
        // Update existing template
        await api.put(`/settings/${endpoint}/${editingTemplate.id}`, templateData);
        setMessage('Template updated successfully');
      } else {
        // Create new template
        await api.post(`/settings/${endpoint}`, templateData);
        setMessage('Template created successfully');
      }
      setShowEditModal(false);
      setEditingTemplate(null);
      setSelectedTemplateType(null);
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

  const allTemplates = [...etsyTemplates, ...shopifyTemplates];

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
          <>
            {/* Etsy Templates Section */}
            <div className="mb-8">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Etsy Templates</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {etsyTemplates.length === 0 ? (
                  <div className="col-span-full text-center py-8 bg-gray-50 rounded-lg">
                    <p className="text-gray-600">No Etsy templates found</p>
                  </div>
                ) : (
                  etsyTemplates.map(template => (
                    <div
                      key={template.id}
                      className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{template.template_title || template.name}</h3>
                          <span className="text-xs px-2 py-1 bg-orange-100 text-orange-700 rounded-full">Etsy</span>
                        </div>
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
                          onClick={() => handleEditTemplate(template, 'etsy')}
                          className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(template.id, 'etsy')}
                          className="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>

            {/* Shopify Templates Section */}
            <div>
              <h3 className="text-xl font-semibold text-gray-900 mb-4">Shopify Templates</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {shopifyTemplates.length === 0 ? (
                  <div className="col-span-full text-center py-8 bg-gray-50 rounded-lg">
                    <p className="text-gray-600">No Shopify templates found</p>
                  </div>
                ) : (
                  shopifyTemplates.map(template => (
                    <div
                      key={template.id}
                      className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow"
                    >
                      <div className="flex justify-between items-start mb-4">
                        <div>
                          <h3 className="text-lg font-semibold text-gray-900">{template.template_title || template.name}</h3>
                          <span className="text-xs px-2 py-1 bg-green-100 text-green-700 rounded-full">Shopify</span>
                        </div>
                      </div>

                      <p className="text-sm text-gray-600 mb-4 line-clamp-2">{template.description || 'No description set'}</p>

                      <div className="space-y-2 mb-4">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Price:</span>
                          <span className="font-medium">${template.price || 0}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Inventory:</span>
                          <span className="font-medium">{template.inventory_quantity || 0}</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-500">Status:</span>
                          <span className="font-medium capitalize">{template.status || 'draft'}</span>
                        </div>
                      </div>

                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleEditTemplate(template, 'shopify')}
                          className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
                        >
                          Edit
                        </button>
                        <button
                          onClick={() => handleDeleteTemplate(template.id, 'shopify')}
                          className="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
                        >
                          Delete
                        </button>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </>
        )}
      </div>

      {/* Template Type Selection Modal */}
      {showTypeSelectionModal && (
        <TemplateTypeSelectionModal
          onSelect={handleTemplateTypeSelected}
          onClose={() => setShowTypeSelectionModal(false)}
        />
      )}

      {/* Template Edit Modal */}
      {showEditModal && (
        <TemplateEditModal
          template={editingTemplate}
          templateType={selectedTemplateType}
          onSave={handleSaveTemplate}
          onClose={() => {
            setShowEditModal(false);
            setEditingTemplate(null);
            setSelectedTemplateType(null);
          }}
        />
      )}
    </div>
  );
};

// Template Type Selection Modal Component
const TemplateTypeSelectionModal = ({ onSelect, onClose }) => {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 !mt-0">
      <div className="bg-white rounded-lg p-8 w-full max-w-md">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Select Template Type</h2>
        <p className="text-gray-600 mb-6">Choose which platform you want to create a template for:</p>

        <div className="space-y-4">
          <button
            onClick={() => onSelect('etsy')}
            className="w-full p-6 bg-orange-50 border-2 border-orange-200 rounded-lg hover:bg-orange-100 hover:border-orange-300 transition-all"
          >
            <div className="flex items-center justify-between">
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900">Etsy Template</h3>
                <p className="text-sm text-gray-600">Create a template for Etsy listings</p>
              </div>
              <svg className="w-6 h-6 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>

          <button
            onClick={() => onSelect('shopify')}
            className="w-full p-6 bg-green-50 border-2 border-green-200 rounded-lg hover:bg-green-100 hover:border-green-300 transition-all"
          >
            <div className="flex items-center justify-between">
              <div className="text-left">
                <h3 className="text-lg font-semibold text-gray-900">Shopify Template</h3>
                <p className="text-sm text-gray-600">Create a template for Shopify products</p>
              </div>
              <svg className="w-6 h-6 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </div>
          </button>
        </div>

        <button
          onClick={onClose}
          className="mt-6 w-full px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

// Template Edit Modal Component
const TemplateEditModal = ({ template, templateType, onSave, onClose }) => {
  const [formData, setFormData] = useState(template);
  const [loading, setLoading] = useState(false);
  const [taxonomies, setTaxonomies] = useState([]);
  const [shopSections, setShopSections] = useState([]);
  const api = useApi();

  useEffect(() => {
    const fetchData = async () => {
      if (templateType === 'etsy') {
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
      }
    };
    fetchData();
  }, [templateType]); // eslint-disable-line react-hooks/exhaustive-deps

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

  // const handleArrayInputChange = (field, value) => {
  //   setFormData(prev => ({ ...prev, [field]: value }));
  // };

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
          <h2 className="text-2xl font-bold text-gray-900">
            {template.id ? 'Edit' : 'Create'} {templateType === 'etsy' ? 'Etsy' : 'Shopify'} Template
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-6">
          {templateType === 'etsy' ? (
            <EtsyTemplateForm
              formData={formData}
              handleInputChange={handleInputChange}
              handleArrayChange={handleArrayChange}
              handleArrayKeyPress={handleArrayKeyPress}
              removeArrayItem={removeArrayItem}
              taxonomies={taxonomies}
              shopSections={shopSections}
            />
          ) : (
            <ShopifyTemplateForm
              formData={formData}
              handleInputChange={handleInputChange}
              handleArrayChange={handleArrayChange}
              handleArrayKeyPress={handleArrayKeyPress}
              removeArrayItem={removeArrayItem}
            />
          )}

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

// Etsy Template Form Component
const EtsyTemplateForm = ({
  formData,
  handleInputChange,
  handleArrayChange,
  handleArrayKeyPress,
  removeArrayItem,
  taxonomies,
  shopSections,
}) => {
  return (
    <>
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

// Shopify Template Form Component
const ShopifyTemplateForm = ({
  formData,
  handleInputChange,
  handleArrayChange,
  handleArrayKeyPress,
  removeArrayItem,
}) => {
  return (
    <>
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
              placeholder="e.g., Shopify Standard Template"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product Title *</label>
            <input
              type="text"
              value={formData.template_title || ''}
              onChange={e => handleInputChange('template_title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
              placeholder="Product title for Shopify"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description || ''}
              onChange={e => handleInputChange('description', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Product description"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Vendor</label>
            <input
              type="text"
              value={formData.vendor || ''}
              onChange={e => handleInputChange('vendor', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Product vendor"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Product Type</label>
            <input
              type="text"
              value={formData.product_type || ''}
              onChange={e => handleInputChange('product_type', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Apparel, Accessories"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tags</label>
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs text-gray-500">{formData.tags ? formData.tags.length : 0} tags</span>
            </div>
            <input
              type="text"
              placeholder="Type tags and press Enter or comma to add"
              onChange={e => handleArrayChange('tags', e.target.value)}
              onKeyPress={e => handleArrayKeyPress('tags', e)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Status</label>
            <select
              value={formData.status || 'draft'}
              onChange={e => handleInputChange('status', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="draft">Draft</option>
              <option value="active">Active</option>
              <option value="archived">Archived</option>
            </select>
          </div>
        </div>

        {/* Pricing & Inventory */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Pricing & Inventory</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Price ($) *</label>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={formData.price || ''}
              onChange={e => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0) {
                  const roundedValue = Math.round(value * 100) / 100;
                  handleInputChange('price', roundedValue);
                } else if (e.target.value === '') {
                  handleInputChange('price', null);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Compare At Price ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={formData.compare_at_price || ''}
              onChange={e => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0) {
                  const roundedValue = Math.round(value * 100) / 100;
                  handleInputChange('compare_at_price', roundedValue);
                } else if (e.target.value === '') {
                  handleInputChange('compare_at_price', null);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Cost Per Item ($)</label>
            <input
              type="number"
              min="0"
              step="0.01"
              placeholder="0.00"
              value={formData.cost_per_item || ''}
              onChange={e => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0) {
                  const roundedValue = Math.round(value * 100) / 100;
                  handleInputChange('cost_per_item', roundedValue);
                } else if (e.target.value === '') {
                  handleInputChange('cost_per_item', null);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.track_inventory || false}
                onChange={e => handleInputChange('track_inventory', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Track Inventory</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Inventory Quantity</label>
            <input
              type="number"
              min="0"
              value={formData.inventory_quantity || ''}
              onChange={e => handleInputChange('inventory_quantity', parseInt(e.target.value) || 0)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Inventory Policy</label>
            <select
              value={formData.inventory_policy || 'deny'}
              onChange={e => handleInputChange('inventory_policy', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="deny">Deny (Stop selling when out of stock)</option>
              <option value="continue">Continue (Allow overselling)</option>
            </select>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Shipping & Product Options */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Shipping</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SKU Prefix</label>
            <input
              type="text"
              value={formData.sku_prefix || ''}
              onChange={e => handleInputChange('sku_prefix', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., PROD-"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Barcode Prefix</label>
            <input
              type="text"
              value={formData.barcode_prefix || ''}
              onChange={e => handleInputChange('barcode_prefix', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Barcode prefix"
            />
          </div>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.requires_shipping || false}
                onChange={e => handleInputChange('requires_shipping', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Requires Shipping</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Weight</label>
            <input
              type="number"
              min="0"
              step="0.01"
              value={formData.weight || ''}
              onChange={e => {
                const value = parseFloat(e.target.value);
                if (!isNaN(value) && value >= 0) {
                  handleInputChange('weight', value);
                } else if (e.target.value === '') {
                  handleInputChange('weight', null);
                }
              }}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Product weight"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Weight Unit</label>
            <select
              value={formData.weight_unit || 'g'}
              onChange={e => handleInputChange('weight_unit', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="g">Grams (g)</option>
              <option value="kg">Kilograms (kg)</option>
              <option value="oz">Ounces (oz)</option>
              <option value="lb">Pounds (lb)</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fulfillment Service</label>
            <input
              type="text"
              value={formData.fulfillment_service || 'manual'}
              onChange={e => handleInputChange('fulfillment_service', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="manual"
            />
          </div>
        </div>

        {/* Variants */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Product Variants</h3>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.has_variants || false}
                onChange={e => handleInputChange('has_variants', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Has Variants</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 1 Name</label>
            <input
              type="text"
              value={formData.option1_name || ''}
              onChange={e => handleInputChange('option1_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Size"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 1 Values</label>
            <input
              type="text"
              placeholder="Type values and press Enter or comma to add"
              onChange={e => handleArrayChange('option1_values', e.target.value)}
              onKeyPress={e => handleArrayKeyPress('option1_values', e)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {formData.option1_values && formData.option1_values.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.option1_values.map((value, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {value}
                    <button
                      type="button"
                      onClick={() => removeArrayItem('option1_values', index)}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 2 Name</label>
            <input
              type="text"
              value={formData.option2_name || ''}
              onChange={e => handleInputChange('option2_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Color"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 2 Values</label>
            <input
              type="text"
              placeholder="Type values and press Enter or comma to add"
              onChange={e => handleArrayChange('option2_values', e.target.value)}
              onKeyPress={e => handleArrayKeyPress('option2_values', e)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {formData.option2_values && formData.option2_values.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.option2_values.map((value, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {value}
                    <button
                      type="button"
                      onClick={() => removeArrayItem('option2_values', index)}
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
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 3 Name</label>
            <input
              type="text"
              value={formData.option3_name || ''}
              onChange={e => handleInputChange('option3_name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Material"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Option 3 Values</label>
            <input
              type="text"
              placeholder="Type values and press Enter or comma to add"
              onChange={e => handleArrayChange('option3_values', e.target.value)}
              onKeyPress={e => handleArrayKeyPress('option3_values', e)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            />
            {formData.option3_values && formData.option3_values.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-2">
                {formData.option3_values.map((value, index) => (
                  <span
                    key={index}
                    className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800"
                  >
                    {value}
                    <button
                      type="button"
                      onClick={() => removeArrayItem('option3_values', index)}
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
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* SEO */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">SEO</h3>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SEO Title</label>
            <input
              type="text"
              value={formData.seo_title || ''}
              onChange={e => handleInputChange('seo_title', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="SEO optimized title"
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">SEO Description</label>
            <textarea
              value={formData.seo_description || ''}
              onChange={e => handleInputChange('seo_description', e.target.value)}
              rows={4}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="SEO optimized description"
            />
          </div>
        </div>

        {/* Tax Settings */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Tax Settings</h3>

          <div>
            <label className="flex items-center space-x-2">
              <input
                type="checkbox"
                checked={formData.is_taxable || false}
                onChange={e => handleInputChange('is_taxable', e.target.checked)}
                className="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
              />
              <span className="text-sm font-medium text-gray-700">Is Taxable</span>
            </label>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Tax Code</label>
            <input
              type="text"
              value={formData.tax_code || ''}
              onChange={e => handleInputChange('tax_code', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="Product tax code"
            />
          </div>
        </div>
      </div>
    </>
  );
};

export default TemplatesTab;
