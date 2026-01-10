import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useAuth } from '../../../hooks/useAuth';
import { useNotifications } from '../../../components/NotificationSystem';
import axios from 'axios';
import { ArrowLeftIcon, PlusIcon, TrashIcon, ArrowUpIcon, ArrowDownIcon, CheckIcon } from '@heroicons/react/24/outline';

const EmailTemplateEditor = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();
  const { id } = useParams();
  const isEditMode = !!id;

  const [loading, setLoading] = useState(isEditMode);
  const [saving, setSaving] = useState(false);

  // Form state
  const [name, setName] = useState('');
  const [templateType, setTemplateType] = useState('marketing');
  const [emailType, setEmailType] = useState('marketing');
  const [subject, setSubject] = useState('');
  const [primaryColor, setPrimaryColor] = useState('#10b981');
  const [secondaryColor, setSecondaryColor] = useState('#059669');
  const [logoUrl, setLogoUrl] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [blocks, setBlocks] = useState([]);
  const [isDefault, setIsDefault] = useState(false);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    if (isEditMode) {
      loadTemplate();
    }
  }, [id]);

  const loadTemplate = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/emails/templates/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      const template = response.data;
      setName(template.name);
      setTemplateType(template.template_type);
      setEmailType(template.email_type);
      setSubject(template.subject);
      setPrimaryColor(template.primary_color);
      setSecondaryColor(template.secondary_color);
      setLogoUrl(template.logo_url || '');
      setIsActive(template.is_active);
      setBlocks(template.blocks || []);
      setIsDefault(template.is_default);
    } catch (error) {
      console.error('Error loading template:', error);
      addNotification('error', 'Failed to load template');
      navigate('/craftflow/emails/templates');
    } finally {
      setLoading(false);
    }
  };

  const addBlock = type => {
    const newBlock = { type };

    switch (type) {
      case 'logo':
        newBlock.src = '{{logo_url}}';
        newBlock.align = 'center';
        break;
      case 'header':
        newBlock.text = 'Header Text';
        newBlock.color = primaryColor;
        break;
      case 'text':
        newBlock.content = 'Your text here...';
        break;
      case 'button':
        newBlock.text = 'Button Text';
        newBlock.url = '#';
        newBlock.bg_color = primaryColor;
        break;
      case 'order_summary':
        newBlock.show_items = true;
        newBlock.show_totals = true;
        break;
      case 'tracking_info':
        newBlock.tracking_number = '{{tracking_number}}';
        break;
      case 'footer':
        newBlock.content = 'Questions? Contact us at {{support_email}}';
        break;
      default:
        break;
    }

    setBlocks([...blocks, newBlock]);
  };

  const removeBlock = index => {
    setBlocks(blocks.filter((_, i) => i !== index));
  };

  const moveBlockUp = index => {
    if (index === 0) return;
    const newBlocks = [...blocks];
    [newBlocks[index - 1], newBlocks[index]] = [newBlocks[index], newBlocks[index - 1]];
    setBlocks(newBlocks);
  };

  const moveBlockDown = index => {
    if (index === blocks.length - 1) return;
    const newBlocks = [...blocks];
    [newBlocks[index], newBlocks[index + 1]] = [newBlocks[index + 1], newBlocks[index]];
    setBlocks(newBlocks);
  };

  const updateBlock = (index, field, value) => {
    const newBlocks = [...blocks];
    newBlocks[index] = { ...newBlocks[index], [field]: value };
    setBlocks(newBlocks);
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!name || !subject) {
      addNotification('error', 'Please fill in all required fields');
      return;
    }

    if (isDefault) {
      addNotification('error', 'Cannot modify default templates');
      return;
    }

    setSaving(true);

    try {
      const templateData = {
        name,
        template_type: templateType,
        email_type: emailType,
        subject,
        blocks,
        primary_color: primaryColor,
        secondary_color: secondaryColor,
        logo_url: logoUrl || undefined,
        is_active: isActive,
      };

      if (isEditMode) {
        await axios.put(`${API_BASE_URL}/api/ecommerce/admin/emails/templates/${id}`, templateData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Template updated successfully');
      } else {
        await axios.post(`${API_BASE_URL}/api/ecommerce/admin/emails/templates`, templateData, {
          headers: { Authorization: `Bearer ${token}` },
        });
        addNotification('success', 'Template created successfully');
      }

      navigate('/craftflow/emails/templates');
    } catch (error) {
      console.error('Error saving template:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to save template');
    } finally {
      setSaving(false);
    }
  };

  const renderBlockEditor = (block, index) => {
    return (
      <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-4">
        <div className="flex items-center justify-between mb-4">
          <span className="text-sm font-semibold text-gray-700 uppercase">{block.type.replace('_', ' ')}</span>
          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => moveBlockUp(index)}
              disabled={index === 0 || isDefault}
              className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
            >
              <ArrowUpIcon className="w-4 h-4" />
            </button>
            <button
              type="button"
              onClick={() => moveBlockDown(index)}
              disabled={index === blocks.length - 1 || isDefault}
              className="p-1 text-gray-600 hover:text-gray-900 disabled:opacity-30"
            >
              <ArrowDownIcon className="w-4 h-4" />
            </button>
            {!isDefault && (
              <button type="button" onClick={() => removeBlock(index)} className="p-1 text-red-600 hover:text-red-700">
                <TrashIcon className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        <div className="space-y-3">
          {block.type === 'logo' && (
            <>
              <input
                type="text"
                value={block.src || ''}
                onChange={e => updateBlock(index, 'src', e.target.value)}
                placeholder="Logo URL or {{logo_url}}"
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
              />
              <select
                value={block.align || 'center'}
                onChange={e => updateBlock(index, 'align', e.target.value)}
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
            </>
          )}

          {block.type === 'header' && (
            <>
              <input
                type="text"
                value={block.text || ''}
                onChange={e => updateBlock(index, 'text', e.target.value)}
                placeholder="Header text"
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
              />
              <input
                type="color"
                value={block.color || primaryColor}
                onChange={e => updateBlock(index, 'color', e.target.value)}
                disabled={isDefault}
                className="w-20 h-10 border border-gray-300 rounded-lg disabled:opacity-50"
              />
            </>
          )}

          {block.type === 'text' && (
            <textarea
              value={block.content || ''}
              onChange={e => updateBlock(index, 'content', e.target.value)}
              placeholder="Text content (use {{variable}} for dynamic values)"
              rows={3}
              disabled={isDefault}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
            />
          )}

          {block.type === 'button' && (
            <>
              <input
                type="text"
                value={block.text || ''}
                onChange={e => updateBlock(index, 'text', e.target.value)}
                placeholder="Button text"
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
              />
              <input
                type="text"
                value={block.url || ''}
                onChange={e => updateBlock(index, 'url', e.target.value)}
                placeholder="Button URL"
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
              />
              <input
                type="color"
                value={block.bg_color || primaryColor}
                onChange={e => updateBlock(index, 'bg_color', e.target.value)}
                disabled={isDefault}
                className="w-20 h-10 border border-gray-300 rounded-lg disabled:opacity-50"
              />
            </>
          )}

          {block.type === 'order_summary' && (
            <div className="space-y-2">
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={block.show_items !== false}
                  onChange={e => updateBlock(index, 'show_items', e.target.checked)}
                  disabled={isDefault}
                  className="rounded disabled:opacity-50"
                />
                <span className="text-sm">Show items</span>
              </label>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={block.show_totals !== false}
                  onChange={e => updateBlock(index, 'show_totals', e.target.checked)}
                  disabled={isDefault}
                  className="rounded disabled:opacity-50"
                />
                <span className="text-sm">Show totals</span>
              </label>
            </div>
          )}

          {block.type === 'tracking_info' && (
            <input
              type="text"
              value={block.tracking_number || ''}
              onChange={e => updateBlock(index, 'tracking_number', e.target.value)}
              placeholder="{{tracking_number}}"
              disabled={isDefault}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
            />
          )}

          {block.type === 'footer' && (
            <textarea
              value={block.content || ''}
              onChange={e => updateBlock(index, 'content', e.target.value)}
              placeholder="Footer content"
              rows={2}
              disabled={isDefault}
              className="w-full px-3 py-2 border border-gray-300 rounded-lg text-sm disabled:bg-gray-100"
            />
          )}
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">Loading template...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-4">
        <button
          onClick={() => navigate('/craftflow/emails/templates')}
          className="p-2 hover:bg-gray-100 rounded-lg transition-colors"
        >
          <ArrowLeftIcon className="w-5 h-5" />
        </button>
        <div>
          <h1 className="text-3xl font-bold text-gray-900">
            {isEditMode ? 'Edit Email Template' : 'Create Email Template'}
          </h1>
          {isDefault && (
            <p className="text-sm text-amber-600 mt-1">⚠️ This is a default template and cannot be modified</p>
          )}
        </div>
      </div>

      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Template Settings */}
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Template Settings</h3>

          <div className="grid md:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
              <input
                type="text"
                value={name}
                onChange={e => setName(e.target.value)}
                required
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Template Type</label>
              <select
                value={templateType}
                onChange={e => setTemplateType(e.target.value)}
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              >
                <option value="transactional">Transactional</option>
                <option value="marketing">Marketing</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Email Type</label>
              <select
                value={emailType}
                onChange={e => setEmailType(e.target.value)}
                disabled={isDefault}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              >
                <option value="order_confirmation">Order Confirmation</option>
                <option value="shipping_notification">Shipping Notification</option>
                <option value="marketing">Marketing</option>
              </select>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Subject Line *</label>
              <input
                type="text"
                value={subject}
                onChange={e => setSubject(e.target.value)}
                required
                disabled={isDefault}
                placeholder="Use {{variables}} for dynamic content"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              />
            </div>
          </div>

          <div className="text-xs text-gray-500 bg-blue-50 p-3 rounded">
            <strong>Variables:</strong> {'{{order_number}}'}, {'{{customer_name}}'}, {'{{tracking_number}}'},{' '}
            {'{{logo_url}}'}
          </div>
        </div>

        {/* Branding */}
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
          <h3 className="text-lg font-semibold text-gray-900">Branding</h3>

          <div className="grid md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Primary Color</label>
              <input
                type="color"
                value={primaryColor}
                onChange={e => setPrimaryColor(e.target.value)}
                disabled={isDefault}
                className="w-full h-10 border border-gray-300 rounded-lg disabled:opacity-50"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Secondary Color</label>
              <input
                type="color"
                value={secondaryColor}
                onChange={e => setSecondaryColor(e.target.value)}
                disabled={isDefault}
                className="w-full h-10 border border-gray-300 rounded-lg disabled:opacity-50"
              />
            </div>

            <div className="md:col-span-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">Logo URL</label>
              <input
                type="text"
                value={logoUrl}
                onChange={e => setLogoUrl(e.target.value)}
                disabled={isDefault}
                placeholder="https://example.com/logo.png"
                className="w-full px-3 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100"
              />
            </div>
          </div>
        </div>

        {/* Block Editor */}
        <div className="bg-white rounded-lg shadow-sm p-6 space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-semibold text-gray-900">Email Content</h3>
            {!isDefault && (
              <div className="relative group">
                <button
                  type="button"
                  className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
                >
                  <PlusIcon className="w-4 h-4" />
                  Add Block
                </button>

                <div className="hidden group-hover:block absolute right-0 mt-2 w-56 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-10">
                  {[
                    'logo',
                    'header',
                    'text',
                    'button',
                    'order_summary',
                    'tracking_info',
                    'shipping_address',
                    'footer',
                  ].map(type => (
                    <button
                      key={type}
                      type="button"
                      onClick={() => addBlock(type)}
                      className="w-full text-left px-4 py-2 text-sm hover:bg-gray-50 capitalize"
                    >
                      {type.replace('_', ' ')}
                    </button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="space-y-4">
            {blocks.length === 0 ? (
              <div className="text-center py-12 text-gray-500">No blocks yet. Click "Add Block" to get started.</div>
            ) : (
              blocks.map((block, index) => renderBlockEditor(block, index))
            )}
          </div>
        </div>

        {/* Status */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <label className="flex items-center gap-2">
            <input
              type="checkbox"
              checked={isActive}
              onChange={e => setIsActive(e.target.checked)}
              disabled={isDefault}
              className="rounded disabled:opacity-50"
            />
            <span className="text-sm font-medium text-gray-700">Active (template will be used for sending)</span>
          </label>
        </div>

        {/* Actions */}
        <div className="flex items-center justify-end gap-4">
          <button
            type="button"
            onClick={() => navigate('/craftflow/emails/templates')}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          {!isDefault && (
            <button
              type="submit"
              disabled={saving}
              className="inline-flex items-center gap-2 px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50"
            >
              <CheckIcon className="w-5 h-5" />
              {saving ? 'Saving...' : isEditMode ? 'Save Changes' : 'Create Template'}
            </button>
          )}
        </div>
      </form>
    </div>
  );
};

export default EmailTemplateEditor;
