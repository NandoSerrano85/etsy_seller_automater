import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const BulkEditModal = ({ selectedListingIds, onClose, onSuccess }) => {
  const api = useApi();
  const [formData, setFormData] = useState({
    description: '',
    price: '',
    quantity: '',
    tags: '',
    materials: '',
    taxonomy_id: '',
    shop_section_id: '',
    shipping_profile_id: '',
    item_weight: '',
    item_weight_unit: 'oz',
    item_length: '',
    item_width: '',
    item_height: '',
    item_dimensions_unit: 'in',
    who_made: 'i_did',
    when_made: 'made_to_order',
    processing_min: '',
    processing_max: '',
    is_taxable: false,
  });
  const [enabledFields, setEnabledFields] = useState({});
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [results, setResults] = useState(null);
  const [dropdownOptions, setDropdownOptions] = useState({
    taxonomies: [],
    shippingProfiles: [],
    shopSections: [],
  });
  const [dropdownLoading, setDropdownLoading] = useState(true);

  useEffect(() => {
    // Fetch dropdown options when modal opens
    fetchDropdownOptions();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchDropdownOptions = async () => {
    setDropdownLoading(true);
    try {
      const [taxonomiesRes, shippingProfilesRes, shopSectionsRes] = await Promise.all([
        api.get('/third-party-listings/options/taxonomies'),
        api.get('/third-party-listings/options/shipping-profiles'),
        api.get('/third-party-listings/options/shop-sections'),
      ]);

      setDropdownOptions({
        taxonomies: taxonomiesRes.taxonomies || [],
        shippingProfiles: shippingProfilesRes.shipping_profiles || [],
        shopSections: shopSectionsRes.shop_sections || [],
      });
    } catch (err) {
      console.error('Error fetching dropdown options:', err);
    } finally {
      setDropdownLoading(false);
    }
  };

  const handleInputChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleFieldToggle = fieldName => {
    setEnabledFields(prev => ({
      ...prev,
      [fieldName]: !prev[fieldName],
    }));
  };

  const handleSubmit = async e => {
    e.preventDefault();
    setLoading(true);
    setError(null);
    setResults(null);

    try {
      // Prepare the data for submission - only include enabled fields
      const updateData = {};

      Object.keys(enabledFields).forEach(fieldName => {
        if (enabledFields[fieldName] && formData[fieldName] !== '') {
          let value = formData[fieldName];

          // Convert numeric fields
          if (['price', 'item_weight', 'item_length', 'item_width', 'item_height'].includes(fieldName)) {
            value = parseFloat(value) || undefined;
          } else if (
            [
              'quantity',
              'processing_min',
              'processing_max',
              'taxonomy_id',
              'shop_section_id',
              'shipping_profile_id',
            ].includes(fieldName)
          ) {
            value = parseInt(value) || undefined;
          } else if (fieldName === 'tags' || fieldName === 'materials') {
            value = value
              .split(',')
              .map(item => item.trim())
              .filter(Boolean);
          }

          if (value !== undefined) {
            updateData[fieldName] = value;
          }
        }
      });

      if (Object.keys(updateData).length === 0) {
        setError('Please enable and fill at least one field to update');
        return;
      }

      const response = await api.post('/third-party-listings/bulk-update', {
        listing_ids: selectedListingIds,
        updates: updateData,
      });

      setResults(response);

      if (response.failure_count === 0) {
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      }
    } catch (err) {
      console.error('Error bulk updating listings:', err);
      setError(err.message || 'Failed to bulk update listings');
    } finally {
      setLoading(false);
    }
  };

  const fieldGroups = [
    {
      title: 'Basic Information',
      fields: [
        { name: 'description', label: 'Description', type: 'textarea', placeholder: 'Enter description...' },
        { name: 'price', label: 'Price ($)', type: 'number', step: '0.01', min: '0', placeholder: '0.00' },
        { name: 'quantity', label: 'Quantity', type: 'number', min: '0', placeholder: '0' },
        { name: 'tags', label: 'Tags (comma separated)', type: 'text', placeholder: 'tag1, tag2, tag3' },
        {
          name: 'materials',
          label: 'Materials (comma separated)',
          type: 'text',
          placeholder: 'material1, material2, material3',
        },
      ],
    },
    {
      title: 'Shop Settings',
      fields: [
        {
          name: 'taxonomy_id',
          label: 'Category (Taxonomy)',
          type: 'select',
          options: [], // Will be populated dynamically
        },
        {
          name: 'shop_section_id',
          label: 'Shop Section',
          type: 'select',
          options: [], // Will be populated dynamically
        },
        {
          name: 'shipping_profile_id',
          label: 'Shipping Profile',
          type: 'select',
          options: [], // Will be populated dynamically
        },
      ],
    },
    {
      title: 'Physical Properties',
      fields: [
        { name: 'item_weight', label: 'Weight', type: 'number', step: '0.01', min: '0', placeholder: '0.00' },
        {
          name: 'item_weight_unit',
          label: 'Weight Unit',
          type: 'select',
          options: [
            { value: 'oz', label: 'oz' },
            { value: 'lb', label: 'lb' },
            { value: 'g', label: 'g' },
            { value: 'kg', label: 'kg' },
          ],
        },
        { name: 'item_length', label: 'Length', type: 'number', step: '0.01', min: '0', placeholder: '0.00' },
        { name: 'item_width', label: 'Width', type: 'number', step: '0.01', min: '0', placeholder: '0.00' },
        { name: 'item_height', label: 'Height', type: 'number', step: '0.01', min: '0', placeholder: '0.00' },
        {
          name: 'item_dimensions_unit',
          label: 'Dimensions Unit',
          type: 'select',
          options: [
            { value: 'in', label: 'inches' },
            { value: 'cm', label: 'cm' },
            { value: 'mm', label: 'mm' },
          ],
        },
      ],
    },
    {
      title: 'Product Details',
      fields: [
        {
          name: 'who_made',
          label: 'Who Made',
          type: 'select',
          options: [
            { value: 'i_did', label: 'I did' },
            { value: 'someone_else', label: 'Someone else' },
            { value: 'collective', label: 'A member of my shop' },
          ],
        },
        {
          name: 'when_made',
          label: 'When Made',
          type: 'select',
          options: [
            { value: 'made_to_order', label: 'Made to order' },
            { value: '2020_2023', label: '2020-2023' },
            { value: '2010_2019', label: '2010-2019' },
            { value: '2000_2009', label: '2000-2009' },
            { value: '1990s', label: '1990s' },
            { value: '1980s', label: '1980s' },
            { value: '1970s', label: '1970s' },
            { value: '1960s', label: '1960s' },
            { value: 'before_1700', label: 'Before 1700' },
          ],
        },
        { name: 'processing_min', label: 'Processing Time Min (days)', type: 'number', min: '1', placeholder: '1' },
        { name: 'processing_max', label: 'Processing Time Max (days)', type: 'number', min: '1', placeholder: '7' },
        { name: 'is_taxable', label: 'This item is taxable', type: 'checkbox' },
      ],
    },
  ];

  const renderField = field => {
    const isEnabled = enabledFields[field.name];
    const fieldProps = {
      name: field.name,
      value: formData[field.name],
      onChange: handleInputChange,
      disabled: !isEnabled,
      className: `w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500 ${
        !isEnabled ? 'bg-gray-100' : ''
      }`,
    };

    if (field.type === 'textarea') {
      return <textarea rows={3} placeholder={field.placeholder} {...fieldProps} />;
    } else if (field.type === 'select') {
      // Get dynamic options for dropdown fields
      let options = field.options;
      if (field.name === 'taxonomy_id') {
        options = [
          { value: '', label: 'Select a category...' },
          ...dropdownOptions.taxonomies.map(tax => ({ value: tax.id, label: tax.name })),
        ];
      } else if (field.name === 'shop_section_id') {
        options = [
          { value: '', label: 'Select a section...' },
          ...dropdownOptions.shopSections.map(section => ({ value: section.id, label: section.name })),
        ];
      } else if (field.name === 'shipping_profile_id') {
        options = [
          { value: '', label: 'Select a shipping profile...' },
          ...dropdownOptions.shippingProfiles.map(profile => ({ value: profile.id, label: profile.name })),
        ];
      }

      return (
        <select {...fieldProps}>
          {options.map(option => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      );
    } else if (field.type === 'checkbox') {
      return (
        <input
          type="checkbox"
          checked={formData[field.name]}
          onChange={handleInputChange}
          disabled={!isEnabled}
          name={field.name}
          className="rounded border-gray-300 text-lavender-500 focus:ring-lavender-500"
        />
      );
    } else {
      return (
        <input type={field.type} step={field.step} min={field.min} placeholder={field.placeholder} {...fieldProps} />
      );
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-start">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">Bulk Edit Listings</h2>
              <p className="text-gray-600 mt-1">Editing {selectedListingIds.length} listings</p>
            </div>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-2xl">
              ×
            </button>
          </div>
        </div>

        {/* Results */}
        {results && (
          <div className="p-6 border-b border-gray-200">
            <div
              className={`rounded-lg p-4 ${
                results.failure_count === 0
                  ? 'bg-green-50 border border-green-200'
                  : 'bg-yellow-50 border border-yellow-200'
              }`}
            >
              <h3 className={`font-semibold ${results.failure_count === 0 ? 'text-green-800' : 'text-yellow-800'}`}>
                Bulk Update Results
              </h3>
              <p className={`mt-2 ${results.failure_count === 0 ? 'text-green-700' : 'text-yellow-700'}`}>
                Successfully updated: {results.success_count} listings
                {results.failure_count > 0 && (
                  <>
                    <br />
                    Failed to update: {results.failure_count} listings
                  </>
                )}
              </p>
              {results.failure_count === 0 && (
                <p className="text-green-600 text-sm mt-2">This modal will close automatically in a moment...</p>
              )}
            </div>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6 space-y-8">
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700">{error}</p>
            </div>
          )}

          {dropdownLoading && (
            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
              <div className="flex items-center">
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-yellow-500 mr-3"></div>
                <p className="text-yellow-800">Loading dropdown options...</p>
              </div>
            </div>
          )}

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-blue-800 text-sm">
              <strong>Note:</strong> Only enabled fields will be updated across all selected listings. Enable a field by
              checking the box next to its label.
            </p>
          </div>

          {fieldGroups.map((group, groupIndex) => (
            <div key={groupIndex} className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-900">{group.title}</h3>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {group.fields.map(field => (
                  <div key={field.name} className="space-y-2">
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={enabledFields[field.name] || false}
                        onChange={() => handleFieldToggle(field.name)}
                        className="rounded border-gray-300 text-lavender-500 focus:ring-lavender-500"
                      />
                      <label className="text-sm font-medium text-gray-700">{field.label}</label>
                    </div>

                    {field.type === 'checkbox' ? (
                      <div className="flex items-center gap-2 ml-6">
                        {renderField(field)}
                        <span className="text-sm text-gray-600">{field.label}</span>
                      </div>
                    ) : (
                      renderField(field)
                    )}

                    {field.name === 'tags' && <p className="text-xs text-gray-500">Maximum 13 tags allowed</p>}
                    {field.name === 'materials' && (
                      <p className="text-xs text-gray-500">Maximum 13 materials allowed</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-6 border-t border-gray-200">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50"
              disabled={loading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-lavender-500 text-white rounded-lg hover:bg-lavender-600 disabled:opacity-50"
              disabled={loading}
            >
              {loading ? 'Updating...' : `Update ${selectedListingIds.length} Listings`}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default BulkEditModal;
