import React, { useState, useEffect } from 'react';
import { useApi } from '../../hooks/useApi';

// Import the original TemplatesTab content as ProductDetailsContent
// We'll create inline versions of Canvas and Size sections here

const TemplatesWithSubtabs = () => {
  const [activeSubtab, setActiveSubtab] = useState('product-details');

  const subtabs = [
    {
      id: 'product-details',
      label: 'Product Details',
      icon: 'M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2',
    },
    {
      id: 'canvas-area',
      label: 'Design Canvas Area',
      icon: 'M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z',
    },
    {
      id: 'size-area',
      label: 'Design Size Area',
      icon: 'M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z',
    },
  ];

  const renderSubtabContent = () => {
    switch (activeSubtab) {
      case 'product-details':
        return <ProductDetailsSection />;
      case 'canvas-area':
        return <CanvasAreaSection />;
      case 'size-area':
        return <SizeAreaSection />;
      default:
        return <ProductDetailsSection />;
    }
  };

  return (
    <div className="space-y-6">
      {/* Subtab Navigation */}
      <div className="card p-4">
        <div className="flex flex-wrap gap-2">
          {subtabs.map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveSubtab(tab.id)}
              className={`flex items-center px-4 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                activeSubtab === tab.id
                  ? 'bg-blue-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
              </svg>
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* Subtab Content */}
      {renderSubtabContent()}
    </div>
  );
};

// ========================
// Product Details Section (Original Templates)
// ========================
const ProductDetailsSection = () => {
  const api = useApi();
  const [etsyTemplates, setEtsyTemplates] = useState([]);
  const [shopifyTemplates, setShopifyTemplates] = useState([]);
  const [craftflowTemplates, setCraftflowTemplates] = useState([]);
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
      const [etsyResponse, shopifyResponse, craftflowResponse] = await Promise.all([
        api.get('/settings/product-template'),
        api.get('/settings/shopify-product-template'),
        api.get('/settings/craftflow-commerce-template'),
      ]);
      setEtsyTemplates(etsyResponse);
      setShopifyTemplates(shopifyResponse);
      setCraftflowTemplates(craftflowResponse);
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
    } else if (type === 'shopify') {
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
        status: 'draft',
        published_scope: 'web',
        seo_title: '',
        seo_description: '',
        is_taxable: true,
        tax_code: '',
        gift_card: false,
        template_suffix: '',
      });
    } else if (type === 'craftflow') {
      setEditingTemplate({
        name: '',
        template_title: '',
        description: '',
        short_description: '',
        product_type: 'physical',
        print_method: 'uvdtf',
        category: 'cup_wraps',
        price: 0.0,
        compare_at_price: null,
        cost: null,
        track_inventory: false,
        inventory_quantity: 0,
        allow_backorder: false,
        digital_file_url: '',
        download_limit: 3,
        meta_title: '',
        meta_description: '',
        is_active: true,
        is_featured: false,
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
    } else if (type === 'shopify') {
      setEditingTemplate({
        ...template,
        tags: template.tags ? template.tags.split(',') : [],
      });
    } else if (type === 'craftflow') {
      setEditingTemplate({
        ...template,
      });
    }
    setShowEditModal(true);
  };

  const handleDeleteTemplate = async (templateId, type) => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      const endpoint =
        type === 'etsy'
          ? 'product-template'
          : type === 'shopify'
            ? 'shopify-product-template'
            : 'craftflow-commerce-template';
      await api.delete(`/settings/${endpoint}/${templateId}`);
      setMessage('Template deleted successfully');
      fetchTemplates();
    } catch (error) {
      console.error('Error deleting template:', error);
      setMessage('Failed to delete template');
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
    <div className="card p-8">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-bold text-gray-900">Product Templates</h2>
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
                  <TemplateCard
                    key={template.id}
                    template={template}
                    type="etsy"
                    onEdit={handleEditTemplate}
                    onDelete={handleDeleteTemplate}
                  />
                ))
              )}
            </div>
          </div>

          {/* Shopify Templates Section */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">Shopify Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {shopifyTemplates.length === 0 ? (
                <div className="col-span-full text-center py-8 bg-gray-50 rounded-lg">
                  <p className="text-gray-600">No Shopify templates found</p>
                </div>
              ) : (
                shopifyTemplates.map(template => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    type="shopify"
                    onEdit={handleEditTemplate}
                    onDelete={handleDeleteTemplate}
                  />
                ))
              )}
            </div>
          </div>

          {/* CraftFlow Templates Section */}
          <div className="mb-8">
            <h3 className="text-xl font-semibold text-gray-900 mb-4">CraftFlow Templates</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {craftflowTemplates.length === 0 ? (
                <div className="col-span-full text-center py-8 bg-gray-50 rounded-lg">
                  <p className="text-gray-600">No CraftFlow templates found</p>
                </div>
              ) : (
                craftflowTemplates.map(template => (
                  <TemplateCard
                    key={template.id}
                    template={template}
                    type="craftflow"
                    onEdit={handleEditTemplate}
                    onDelete={handleDeleteTemplate}
                  />
                ))
              )}
            </div>
          </div>
        </>
      )}

      {/* Type Selection Modal */}
      {showTypeSelectionModal && (
        <TypeSelectionModal onSelect={handleTemplateTypeSelected} onClose={() => setShowTypeSelectionModal(false)} />
      )}
    </div>
  );
};

// Template Card Component
const TemplateCard = ({ template, type, onEdit, onDelete }) => {
  const typeColors = {
    etsy: 'bg-orange-100 text-orange-700',
    shopify: 'bg-green-100 text-green-700',
    craftflow: 'bg-purple-100 text-purple-700',
  };

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-gray-900">{template.template_title || template.name}</h3>
          <span className={`text-xs px-2 py-1 rounded-full ${typeColors[type]}`}>
            {type.charAt(0).toUpperCase() + type.slice(1)}
          </span>
        </div>
      </div>

      <p className="text-sm text-gray-600 mb-4 line-clamp-2">
        {template.title || template.description || 'No description set'}
      </p>

      <div className="space-y-2 mb-4">
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">Price:</span>
          <span className="font-medium">${template.price || 0}</span>
        </div>
        <div className="flex justify-between text-sm">
          <span className="text-gray-500">{type === 'shopify' ? 'Inventory' : 'Quantity'}:</span>
          <span className="font-medium">{template.inventory_quantity || template.quantity || 0}</span>
        </div>
      </div>

      <div className="flex space-x-2">
        <button
          onClick={() => onEdit(template, type)}
          className="flex-1 px-3 py-2 bg-blue-500 text-white text-sm rounded-lg hover:bg-blue-600 transition-colors"
        >
          Edit
        </button>
        <button
          onClick={() => onDelete(template.id, type)}
          className="px-3 py-2 bg-red-500 text-white text-sm rounded-lg hover:bg-red-600 transition-colors"
        >
          Delete
        </button>
      </div>
    </div>
  );
};

// Type Selection Modal
const TypeSelectionModal = ({ onSelect, onClose }) => {
  const types = [
    { id: 'etsy', name: 'Etsy', description: 'Create a template for Etsy listings', color: 'orange' },
    { id: 'shopify', name: 'Shopify', description: 'Create a template for Shopify products', color: 'green' },
    { id: 'craftflow', name: 'CraftFlow', description: 'Create a template for CraftFlow Commerce', color: 'purple' },
  ];

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
        <h3 className="text-xl font-semibold text-gray-900 mb-6">Select Template Type</h3>
        <div className="space-y-4">
          {types.map(type => (
            <button
              key={type.id}
              onClick={() => onSelect(type.id)}
              className={`w-full p-4 border-2 rounded-lg text-left hover:border-${type.color}-500 hover:bg-${type.color}-50 transition-all`}
            >
              <h4 className="font-semibold text-gray-900">{type.name}</h4>
              <p className="text-sm text-gray-600">{type.description}</p>
            </button>
          ))}
        </div>
        <button
          onClick={onClose}
          className="mt-6 w-full px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
        >
          Cancel
        </button>
      </div>
    </div>
  );
};

// ========================
// Canvas Area Section
// ========================
const CanvasAreaSection = () => {
  const api = useApi();
  const [canvasConfigs, setCanvasConfigs] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingCanvas, setEditingCanvas] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchData = async () => {
    try {
      setLoading(true);
      const [canvasResponse, templatesResponse] = await Promise.all([
        api.get('/settings/canvas-config'),
        api.get('/settings/product-template'),
      ]);
      setCanvasConfigs(canvasResponse);
      setTemplates(templatesResponse);
      setMessage('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessage('Failed to load canvas configurations');
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
      spacing_width_inches: 0.125,
      spacing_height_inches: 0.125,
      dpi: 300,
      description: '',
      is_active: true,
      is_stretch: true,
    });
    setShowModal(true);
  };

  const handleEditCanvas = config => {
    setEditingCanvas({ ...config });
    setShowModal(true);
  };

  const handleDeleteCanvas = async configId => {
    if (!window.confirm('Are you sure you want to delete this canvas configuration?')) {
      return;
    }

    try {
      const canvas = canvasConfigs.find(c => c.id === configId);
      if (canvas) {
        await api.delete(`/settings/${canvas.product_template_id}/canvas-config/${configId}`);
        setMessage('Canvas configuration deleted successfully');
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting canvas config:', error);
      setMessage('Failed to delete canvas configuration');
    }
  };

  const handleSaveCanvas = async configData => {
    try {
      if (editingCanvas.id) {
        await api.put(`/settings/${editingCanvas.product_template_id}/canvas-config/${editingCanvas.id}`, configData);
        setMessage('Canvas configuration updated successfully');
      } else {
        await api.post(`/settings/${configData.product_template_id}/canvas-config`, configData);
        setMessage('Canvas configuration created successfully');
      }
      setShowModal(false);
      setEditingCanvas(null);
      fetchData();
    } catch (error) {
      console.error('Error saving canvas config:', error);
      setMessage(error.message || 'Failed to save canvas configuration');
    }
  };

  return (
    <div className="card p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Design Canvas Area</h2>
          <p className="text-gray-600 mt-1">Configure canvas dimensions for your mockup designs</p>
        </div>
        <button
          onClick={handleCreateCanvas}
          className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
        >
          Add Canvas Config
        </button>
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
          <p className="text-gray-600">Loading canvas configurations...</p>
        </div>
      ) : canvasConfigs.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No canvas configurations found</h3>
          <p className="text-gray-600 mb-4">
            Create your first canvas configuration to define canvas dimensions for your templates.
          </p>
          <button
            onClick={handleCreateCanvas}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Create Canvas Config
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {canvasConfigs.map(config => (
            <div key={config.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-gray-900 mb-1">{config.name}</h4>
                <p className="text-sm text-gray-500">{config.template_name}</p>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Canvas Size:</span>
                  <span className="font-medium">
                    {config.width_inches}" x {config.height_inches}"
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Spacing:</span>
                  <span className="font-medium">
                    W: {config.spacing_width_inches || 0.125}", H: {config.spacing_height_inches || 0.125}"
                  </span>
                </div>
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">DPI:</span>
                  <span className="font-medium">{config.dpi || 300}</span>
                </div>
                {config.description && <div className="text-sm text-gray-600 mt-2">{config.description}</div>}
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

      {/* Canvas Modal */}
      {showModal && (
        <CanvasModal
          config={editingCanvas}
          templates={templates}
          onSave={handleSaveCanvas}
          onClose={() => {
            setShowModal(false);
            setEditingCanvas(null);
          }}
        />
      )}
    </div>
  );
};

// Canvas Modal Component
const CanvasModal = ({ config, templates, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    product_template_id: config?.product_template_id || null,
    name: config?.name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    spacing_width_inches: config?.spacing_width_inches || 0.125,
    spacing_height_inches: config?.spacing_height_inches || 0.125,
    dpi: config?.dpi || 300,
    description: config?.description || '',
    is_active: config?.is_active !== undefined ? config.is_active : true,
    is_stretch: config?.is_stretch !== undefined ? config.is_stretch : true,
  });
  const [loading, setLoading] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(!config?.id && !config?.product_template_id);

  const handleSubmit = async e => {
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

  const handleTemplateSelect = template => {
    setFormData(prev => ({ ...prev, product_template_id: template.id }));
    setShowTemplateSelector(false);
  };

  if (showTemplateSelector) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Select Template for Canvas Configuration</h3>

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
              {templates.map(template => (
                <div
                  key={template.id}
                  onClick={() => handleTemplateSelect(template)}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h4>
                  {template.template_title && <p className="text-sm text-gray-600 mb-2">{template.template_title}</p>}
                  <div className="text-xs text-gray-500 space-y-1">
                    {template.price && <div>Price: ${template.price}</div>}
                    {template.type && <div>Type: {template.type}</div>}
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
          {!config?.id && (
            <button onClick={() => setShowTemplateSelector(true)} className="text-sm text-blue-600 hover:text-blue-800">
              Change Template
            </button>
          )}
        </div>

        <div className="mb-4 p-3 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600">
            <strong>Selected Template:</strong>{' '}
            {templates.find(t => t.id === formData.product_template_id)?.name || 'Unknown'}
          </p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Canvas Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., UVDTF Decal"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width (inches) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.width_inches}
                onChange={e => handleInputChange('width_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (inches) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.height_inches}
                onChange={e => handleInputChange('height_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width Spacing *</label>
              <input
                type="number"
                step="0.01"
                value={formData.spacing_width_inches}
                onChange={e => handleInputChange('spacing_width_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height Spacing *</label>
              <input
                type="number"
                step="0.01"
                value={formData.spacing_height_inches}
                onChange={e => handleInputChange('spacing_height_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">DPI *</label>
            <select
              value={formData.dpi}
              onChange={e => handleInputChange('dpi', parseInt(e.target.value))}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value={150}>150 DPI</option>
              <option value={200}>200 DPI</option>
              <option value={300}>300 DPI (Standard)</option>
              <option value={400}>400 DPI</option>
              <option value={600}>600 DPI</option>
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={e => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
            />
          </div>

          <div className="flex space-x-4">
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={e => handleInputChange('is_active', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Active</span>
            </label>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_stretch}
                onChange={e => handleInputChange('is_stretch', e.target.checked)}
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
                loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {loading ? 'Saving...' : config?.id ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// ========================
// Size Area Section
// ========================
const SizeAreaSection = () => {
  const api = useApi();
  const [sizeConfigs, setSizeConfigs] = useState([]);
  const [templates, setTemplates] = useState([]);
  const [canvasConfigs, setCanvasConfigs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [editingSize, setEditingSize] = useState(null);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchData = async () => {
    try {
      setLoading(true);
      const [sizeResponse, templatesResponse, canvasResponse] = await Promise.all([
        api.get('/settings/size-config'),
        api.get('/settings/product-template'),
        api.get('/settings/canvas-config'),
      ]);
      setSizeConfigs(sizeResponse);
      setTemplates(templatesResponse);
      setCanvasConfigs(canvasResponse);
      setMessage('');
    } catch (error) {
      console.error('Error fetching data:', error);
      setMessage('Failed to load size configurations');
    } finally {
      setLoading(false);
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
      is_active: true,
    });
    setShowModal(true);
  };

  const handleEditSize = config => {
    setEditingSize({ ...config });
    setShowModal(true);
  };

  const handleDeleteSize = async configId => {
    if (!window.confirm('Are you sure you want to delete this size configuration?')) {
      return;
    }

    try {
      const size = sizeConfigs.find(s => s.id === configId);
      if (size) {
        await api.delete(`/settings/${size.product_template_id}/${size.canvas_id}/size-config/${configId}`);
        setMessage('Size configuration deleted successfully');
        fetchData();
      }
    } catch (error) {
      console.error('Error deleting size config:', error);
      setMessage('Failed to delete size configuration');
    }
  };

  const handleSaveSize = async configData => {
    try {
      if (editingSize.id) {
        await api.put(
          `/settings/${editingSize.product_template_id}/${editingSize.canvas_id}/size-config/${editingSize.id}`,
          configData
        );
        setMessage('Size configuration updated successfully');
      } else {
        await api.post(`/settings/${configData.product_template_id}/${configData.canvas_id}/size-config`, configData);
        setMessage('Size configuration created successfully');
      }
      setShowModal(false);
      setEditingSize(null);
      fetchData();
    } catch (error) {
      console.error('Error saving size config:', error);
      setMessage(error.message || 'Failed to save size configuration');
    }
  };

  return (
    <div className="card p-8">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Design Size Area</h2>
          <p className="text-gray-600 mt-1">Configure size dimensions for your design templates</p>
        </div>
        <button
          onClick={handleCreateSize}
          className="px-6 py-3 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
        >
          Add Size Config
        </button>
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
          <p className="text-gray-600">Loading size configurations...</p>
        </div>
      ) : sizeConfigs.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-gray-400 mb-4">
            <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"
              />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No size configurations found</h3>
          <p className="text-gray-600 mb-4">
            Create your first size configuration to define dimensions for your templates.
          </p>
          <button
            onClick={handleCreateSize}
            className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Create Size Config
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sizeConfigs.map(config => (
            <div key={config.id} className="bg-white border rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow">
              <div className="mb-4">
                <h4 className="text-lg font-semibold text-gray-900 mb-1">{config.name}</h4>
                <div className="text-sm text-gray-500 space-y-0.5">
                  <div>Canvas: {config.canvas_name || 'Unknown'}</div>
                  <div>Template: {config.template_name || 'Unknown'}</div>
                </div>
              </div>

              <div className="space-y-2 mb-4">
                <div className="flex justify-between text-sm">
                  <span className="text-gray-500">Size:</span>
                  <span className="font-medium">
                    {config.width_inches}" x {config.height_inches}"
                  </span>
                </div>
                {config.description && <div className="text-sm text-gray-600 mt-2">{config.description}</div>}
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

      {/* Size Modal */}
      {showModal && (
        <SizeModal
          config={editingSize}
          templates={templates}
          canvasConfigs={canvasConfigs}
          onSave={handleSaveSize}
          onClose={() => {
            setShowModal(false);
            setEditingSize(null);
          }}
        />
      )}
    </div>
  );
};

// Size Modal Component
const SizeModal = ({ config, templates, canvasConfigs, onSave, onClose }) => {
  const [formData, setFormData] = useState({
    product_template_id: config?.product_template_id || null,
    canvas_id: config?.canvas_id || null,
    name: config?.name || '',
    width_inches: config?.width_inches || 0,
    height_inches: config?.height_inches || 0,
    description: config?.description || '',
    is_active: config?.is_active !== undefined ? config.is_active : true,
  });
  const [loading, setLoading] = useState(false);
  const [step, setStep] = useState(!config?.id ? 'template' : 'form'); // 'template', 'canvas', 'form'

  const filteredCanvasConfigs = canvasConfigs.filter(
    canvas => canvas.product_template_id === formData.product_template_id
  );

  const handleSubmit = async e => {
    e.preventDefault();
    if (!formData.product_template_id || !formData.canvas_id) {
      alert('Please select a template and canvas');
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

  if (step === 'template') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Step 1: Select Template</h3>

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
              {templates.map(template => (
                <div
                  key={template.id}
                  onClick={() => {
                    setFormData(prev => ({ ...prev, product_template_id: template.id, canvas_id: null }));
                    setStep('canvas');
                  }}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">{template.name}</h4>
                  {template.template_title && <p className="text-sm text-gray-600">{template.template_title}</p>}
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

  if (step === 'canvas') {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
          <h3 className="text-xl font-semibold text-gray-900 mb-6">Step 2: Select Canvas</h3>

          <div className="mb-4 p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Template:</strong> {templates.find(t => t.id === formData.product_template_id)?.name}
            </p>
          </div>

          {filteredCanvasConfigs.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-600 mb-4">No canvas configurations found for this template.</p>
              <button
                onClick={() => setStep('template')}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors mr-2"
              >
                Back
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
              {filteredCanvasConfigs.map(canvas => (
                <div
                  key={canvas.id}
                  onClick={() => {
                    setFormData(prev => ({ ...prev, canvas_id: canvas.id }));
                    setStep('form');
                  }}
                  className="bg-white border-2 border-gray-200 rounded-lg p-4 cursor-pointer hover:border-blue-500 hover:shadow-md transition-all"
                >
                  <h4 className="text-lg font-semibold text-gray-900 mb-2">{canvas.name}</h4>
                  <div className="text-xs text-gray-500">
                    {canvas.width_inches}" x {canvas.height_inches}"
                  </div>
                </div>
              ))}
            </div>
          )}

          <div className="flex justify-end mt-6">
            <button
              onClick={() => setStep('template')}
              className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors mr-2"
            >
              Back
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
        <h3 className="text-xl font-semibold text-gray-900 mb-6">
          {config?.id ? 'Edit Size Configuration' : 'Create Size Configuration'}
        </h3>

        <div className="mb-4 space-y-2">
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Template:</strong> {templates.find(t => t.id === formData.product_template_id)?.name}
            </p>
          </div>
          <div className="p-3 bg-gray-50 rounded-lg">
            <p className="text-sm text-gray-600">
              <strong>Canvas:</strong> {canvasConfigs.find(c => c.id === formData.canvas_id)?.name}
            </p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Size Name *</label>
            <input
              type="text"
              value={formData.name}
              onChange={e => handleInputChange('name', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              placeholder="e.g., Adult+, Adult, Youth"
              required
            />
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Width (inches) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.width_inches}
                onChange={e => handleInputChange('width_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Height (inches) *</label>
              <input
                type="number"
                step="0.01"
                value={formData.height_inches}
                onChange={e => handleInputChange('height_inches', parseFloat(e.target.value) || 0)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                required
              />
            </div>
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
            <textarea
              value={formData.description}
              onChange={e => handleInputChange('description', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              rows="2"
            />
          </div>

          <div>
            <label className="flex items-center">
              <input
                type="checkbox"
                checked={formData.is_active}
                onChange={e => handleInputChange('is_active', e.target.checked)}
                className="mr-2"
              />
              <span className="text-sm text-gray-700">Active</span>
            </label>
          </div>

          <div className="flex space-x-4 pt-4">
            <button
              type="button"
              onClick={() => (!config?.id ? setStep('canvas') : onClose())}
              className="flex-1 px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              {!config?.id ? 'Back' : 'Cancel'}
            </button>
            <button
              type="submit"
              disabled={loading}
              className={`flex-1 px-4 py-2 rounded-lg font-medium transition-colors ${
                loading ? 'bg-gray-400 text-white cursor-not-allowed' : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {loading ? 'Saving...' : config?.id ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default TemplatesWithSubtabs;
