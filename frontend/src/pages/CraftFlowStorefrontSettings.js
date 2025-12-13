import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import { PaintBrushIcon, PhotoIcon, CheckCircleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';

const CraftFlowStorefrontSettings = () => {
  const { token, user } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [settings, setSettings] = useState({
    store_name: '',
    store_description: '',
    logo_url: '',
    primary_color: '#10b981', // Default sage/emerald green
    secondary_color: '#059669',
    accent_color: '#34d399',
    text_color: '#111827',
    background_color: '#ffffff',
  });

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';
  const STOREFRONT_URL = window.location.origin.replace('3000', '3001');

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/storefront-settings/`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.data) {
        setSettings({
          store_name: response.data.store_name || user?.shop_name || '',
          store_description: response.data.store_description || '',
          logo_url: response.data.logo_url || '',
          primary_color: response.data.primary_color || '#10b981',
          secondary_color: response.data.secondary_color || '#059669',
          accent_color: response.data.accent_color || '#34d399',
          text_color: response.data.text_color || '#111827',
          background_color: response.data.background_color || '#ffffff',
        });
      }
    } catch (error) {
      console.error('Error loading storefront settings:', error);
      // If settings don't exist yet, use defaults
      if (error.response?.status !== 404) {
        addNotification('error', 'Failed to load storefront settings');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = e => {
    const { name, value } = e.target;
    setSettings(prev => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleColorChange = (colorField, value) => {
    setSettings(prev => ({
      ...prev,
      [colorField]: value,
    }));
  };

  const resetToDefaults = () => {
    if (window.confirm('Are you sure you want to reset all colors to defaults?')) {
      setSettings(prev => ({
        ...prev,
        primary_color: '#10b981',
        secondary_color: '#059669',
        accent_color: '#34d399',
        text_color: '#111827',
        background_color: '#ffffff',
      }));
    }
  };

  const handleSubmit = async e => {
    e.preventDefault();

    try {
      setSaving(true);

      await axios.post(`${API_BASE_URL}/api/ecommerce/storefront-settings/`, settings, {
        headers: { Authorization: `Bearer ${token}` },
      });

      addNotification('success', 'Storefront settings saved successfully');
    } catch (error) {
      console.error('Error saving storefront settings:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save storefront settings';
      addNotification('error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <PaintBrushIcon className="w-8 h-8 mr-3 text-sage-600" />
            Storefront Branding
          </h1>
          <p className="text-gray-600">Customize your storefront appearance and branding</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Settings Form */}
          <div className="lg:col-span-2">
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* Store Information */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4">Store Information</h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Store Name</label>
                    <input
                      type="text"
                      name="store_name"
                      value={settings.store_name}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                      placeholder="My Craft Shop"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Store Description</label>
                    <textarea
                      name="store_description"
                      value={settings.store_description}
                      onChange={handleInputChange}
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                      placeholder="Custom designs and prints for all occasions"
                    />
                  </div>
                </div>
              </div>

              {/* Logo */}
              <div className="bg-white rounded-lg shadow p-6">
                <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                  <PhotoIcon className="w-5 h-5 mr-2" />
                  Company Logo
                </h2>

                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Logo URL</label>
                    <input
                      type="url"
                      name="logo_url"
                      value={settings.logo_url}
                      onChange={handleInputChange}
                      className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
                      placeholder="https://example.com/logo.png"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Recommended size: 200x200px or larger (square format works best)
                    </p>
                  </div>

                  {settings.logo_url && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-700 mb-2">Logo Preview</p>
                      <div className="border border-gray-300 rounded-lg p-4 bg-gray-50">
                        <img
                          src={settings.logo_url}
                          alt="Company Logo"
                          className="h-24 w-auto mx-auto"
                          onError={e => {
                            e.target.src =
                              'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iMjAwIiBoZWlnaHQ9IjIwMCIgZmlsbD0iI2VlZSIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LWZhbWlseT0ic2Fucy1zZXJpZiIgZm9udC1zaXplPSIxNCIgZmlsbD0iIzk5OSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZHk9Ii4zZW0iPkltYWdlIEVycm9yPC90ZXh0Pjwvc3ZnPg==';
                          }}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Brand Colors */}
              <div className="bg-white rounded-lg shadow p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-lg font-semibold text-gray-900 flex items-center">
                    <PaintBrushIcon className="w-5 h-5 mr-2" />
                    Brand Colors
                  </h2>
                  <button
                    type="button"
                    onClick={resetToDefaults}
                    className="flex items-center px-3 py-1 text-sm text-gray-600 hover:text-gray-800 hover:bg-gray-100 rounded-md"
                  >
                    <ArrowPathIcon className="w-4 h-4 mr-1" />
                    Reset to Defaults
                  </button>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <ColorPicker
                    label="Primary Color"
                    description="Main brand color (buttons, links)"
                    value={settings.primary_color}
                    onChange={value => handleColorChange('primary_color', value)}
                  />

                  <ColorPicker
                    label="Secondary Color"
                    description="Accent elements"
                    value={settings.secondary_color}
                    onChange={value => handleColorChange('secondary_color', value)}
                  />

                  <ColorPicker
                    label="Accent Color"
                    description="Highlights and badges"
                    value={settings.accent_color}
                    onChange={value => handleColorChange('accent_color', value)}
                  />

                  <ColorPicker
                    label="Text Color"
                    description="Primary text color"
                    value={settings.text_color}
                    onChange={value => handleColorChange('text_color', value)}
                  />

                  <ColorPicker
                    label="Background Color"
                    description="Page background"
                    value={settings.background_color}
                    onChange={value => handleColorChange('background_color', value)}
                  />
                </div>
              </div>

              {/* Action Buttons */}
              <div className="flex items-center justify-end space-x-4">
                <button
                  type="button"
                  onClick={() => navigate('/craftflow/dashboard')}
                  className="px-6 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={saving}
                  className={`flex items-center px-6 py-2 rounded-md text-white ${
                    saving ? 'bg-gray-400 cursor-not-allowed' : 'bg-sage-600 hover:bg-sage-700'
                  }`}
                >
                  {saving ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    <>
                      <CheckCircleIcon className="w-4 h-4 mr-2" />
                      Save Settings
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>

          {/* Preview Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6 sticky top-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">Preview</h3>

              <div className="space-y-4">
                {/* Store Preview */}
                <div className="border rounded-lg p-4" style={{ backgroundColor: settings.background_color }}>
                  {settings.logo_url && (
                    <div className="mb-4 text-center">
                      <img
                        src={settings.logo_url}
                        alt="Logo Preview"
                        className="h-12 w-auto mx-auto"
                        onError={e => {
                          e.target.style.display = 'none';
                        }}
                      />
                    </div>
                  )}

                  <h4 className="font-bold text-lg mb-2" style={{ color: settings.text_color }}>
                    {settings.store_name || 'Your Store Name'}
                  </h4>

                  <p className="text-sm mb-3" style={{ color: settings.text_color, opacity: 0.7 }}>
                    {settings.store_description || 'Store description will appear here'}
                  </p>

                  <button
                    type="button"
                    className="w-full py-2 px-4 rounded-md text-white text-sm font-medium mb-2"
                    style={{ backgroundColor: settings.primary_color }}
                  >
                    Primary Button
                  </button>

                  <button
                    type="button"
                    className="w-full py-2 px-4 rounded-md text-white text-sm font-medium mb-2"
                    style={{ backgroundColor: settings.secondary_color }}
                  >
                    Secondary Button
                  </button>

                  <div className="flex items-center space-x-2">
                    <span
                      className="px-3 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: settings.accent_color }}
                    >
                      New
                    </span>
                    <span
                      className="px-3 py-1 rounded-full text-xs font-medium text-white"
                      style={{ backgroundColor: settings.accent_color }}
                    >
                      Sale
                    </span>
                  </div>
                </div>

                {/* Color Palette */}
                <div>
                  <p className="text-sm font-medium text-gray-700 mb-2">Color Palette</p>
                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <div
                        className="h-12 rounded-lg border border-gray-200"
                        style={{ backgroundColor: settings.primary_color }}
                      />
                      <p className="text-xs text-gray-600 mt-1 text-center">Primary</p>
                    </div>
                    <div>
                      <div
                        className="h-12 rounded-lg border border-gray-200"
                        style={{ backgroundColor: settings.secondary_color }}
                      />
                      <p className="text-xs text-gray-600 mt-1 text-center">Secondary</p>
                    </div>
                    <div>
                      <div
                        className="h-12 rounded-lg border border-gray-200"
                        style={{ backgroundColor: settings.accent_color }}
                      />
                      <p className="text-xs text-gray-600 mt-1 text-center">Accent</p>
                    </div>
                  </div>
                </div>

                {/* View Storefront Link */}
                <div className="pt-4 border-t border-gray-200">
                  <a
                    href={STOREFRONT_URL}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center justify-center w-full py-2 px-4 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-md text-sm font-medium transition-colors"
                  >
                    <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14"
                      />
                    </svg>
                    View Live Storefront
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

// Color Picker Component
const ColorPicker = ({ label, description, value, onChange }) => {
  const [hexValue, setHexValue] = useState(value);

  useEffect(() => {
    setHexValue(value);
  }, [value]);

  const handleHexChange = e => {
    const newValue = e.target.value;
    setHexValue(newValue);
    if (/^#[0-9A-F]{6}$/i.test(newValue)) {
      onChange(newValue);
    }
  };

  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label}</label>
      <p className="text-xs text-gray-500 mb-2">{description}</p>
      <div className="flex items-center space-x-2">
        <input
          type="color"
          value={value}
          onChange={e => {
            onChange(e.target.value);
            setHexValue(e.target.value);
          }}
          className="h-10 w-16 rounded border border-gray-300 cursor-pointer"
        />
        <input
          type="text"
          value={hexValue}
          onChange={handleHexChange}
          className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500 font-mono text-sm"
          placeholder="#000000"
          pattern="^#[0-9A-Fa-f]{6}$"
        />
      </div>
    </div>
  );
};

export default CraftFlowStorefrontSettings;
