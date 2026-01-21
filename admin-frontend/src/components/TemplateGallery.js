import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from './NotificationSystem';
import { PlusIcon, EyeIcon, PencilIcon, TrashIcon, PhotoIcon } from '@heroicons/react/24/outline';

const TemplateGallery = ({ onCreateNew, onEditTemplate }) => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();

  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);

      const response = await fetch('/api/templates/', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load templates');
      }

      const data = await response.json();
      setTemplates(data.templates || []);
    } catch (error) {
      console.error('Error loading templates:', error);
      addNotification('Failed to load templates', 'error');
    } finally {
      setLoading(false);
    }
  };

  const deleteTemplate = async templateId => {
    if (!window.confirm('Are you sure you want to delete this template?')) {
      return;
    }

    try {
      const response = await fetch(`/api/templates/${templateId}`, {
        method: 'DELETE',
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to delete template');
      }

      addNotification('Template deleted successfully', 'success');
      loadTemplates(); // Reload templates
    } catch (error) {
      console.error('Error deleting template:', error);
      addNotification('Failed to delete template', 'error');
    }
  };

  const previewTemplate = template => {
    setSelectedTemplate(template);
  };

  if (loading) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
        <p className="text-sage-600">Loading templates...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-900">Template Gallery</h2>
          <p className="text-gray-600">Manage your product templates</p>
        </div>
        {onCreateNew && (
          <button
            onClick={onCreateNew}
            className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Create New Template
          </button>
        )}
      </div>

      {/* Templates Grid */}
      {templates.length === 0 ? (
        <div className="text-center py-12">
          <PhotoIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No templates yet</h3>
          <p className="text-gray-600 mb-4">Create your first template to get started</p>
          {onCreateNew && (
            <button
              onClick={onCreateNew}
              className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 mx-auto"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Create Template
            </button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {templates.map(template => (
            <div
              key={template.id}
              className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-shadow"
            >
              {/* Template Image */}
              <div className="aspect-w-16 aspect-h-12 bg-gray-200">
                <img src={template.background_image_url} alt={template.name} className="w-full h-48 object-cover" />
              </div>

              {/* Template Info */}
              <div className="p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-1">{template.name}</h3>

                {template.description && (
                  <p className="text-sm text-gray-600 mb-2 line-clamp-2">{template.description}</p>
                )}

                <div className="flex items-center justify-between mb-3">
                  <span className="text-xs text-gray-500">
                    {template.design_areas.length} design area{template.design_areas.length !== 1 ? 's' : ''}
                  </span>
                  {template.category && (
                    <span className="inline-block bg-gray-100 text-gray-800 text-xs px-2 py-1 rounded">
                      {template.category}
                    </span>
                  )}
                </div>

                {/* Actions */}
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => previewTemplate(template)}
                    className="flex items-center px-3 py-1 text-sm bg-blue-50 text-blue-600 rounded hover:bg-blue-100"
                    title="Preview"
                  >
                    <EyeIcon className="w-4 h-4 mr-1" />
                    Preview
                  </button>

                  {onEditTemplate && (
                    <button
                      onClick={() => onEditTemplate(template)}
                      className="flex items-center px-3 py-1 text-sm bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
                      title="Edit"
                    >
                      <PencilIcon className="w-4 h-4 mr-1" />
                      Edit
                    </button>
                  )}

                  <button
                    onClick={() => deleteTemplate(template.id)}
                    className="flex items-center px-3 py-1 text-sm bg-red-50 text-red-600 rounded hover:bg-red-100"
                    title="Delete"
                  >
                    <TrashIcon className="w-4 h-4 mr-1" />
                    Delete
                  </button>
                </div>

                <div className="text-xs text-gray-400 mt-2">
                  Created: {new Date(template.created_at).toLocaleDateString()}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Preview Modal */}
      {selectedTemplate && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-full overflow-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <div>
                <h3 className="text-lg font-semibold">{selectedTemplate.name}</h3>
                {selectedTemplate.description && (
                  <p className="text-gray-600 text-sm">{selectedTemplate.description}</p>
                )}
              </div>
              <button onClick={() => setSelectedTemplate(null)} className="text-gray-400 hover:text-gray-600">
                ×
              </button>
            </div>

            <div className="p-6">
              <div className="relative">
                <img
                  src={selectedTemplate.background_image_url}
                  alt={selectedTemplate.name}
                  className="max-w-full h-auto mx-auto rounded border"
                />

                {/* Overlay design areas for preview */}
                <div className="absolute inset-0 pointer-events-none">
                  {selectedTemplate.design_areas.map((area, index) => (
                    <div
                      key={index}
                      className="absolute border-2 border-red-500 border-dashed bg-red-500 bg-opacity-10"
                      style={{
                        left: `${(area.x / selectedTemplate.background_image_url.naturalWidth || 800) * 100}%`,
                        top: `${(area.y / selectedTemplate.background_image_url.naturalHeight || 600) * 100}%`,
                        width: `${(area.width / selectedTemplate.background_image_url.naturalWidth || 800) * 100}%`,
                        height: `${(area.height / selectedTemplate.background_image_url.naturalHeight || 600) * 100}%`,
                      }}
                    >
                      <span className="absolute -top-6 left-0 text-xs text-red-600 bg-white px-1 rounded">
                        {area.name}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              <div className="mt-4">
                <h4 className="font-semibold text-gray-900 mb-2">Design Areas:</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {selectedTemplate.design_areas.map((area, index) => (
                    <div key={index} className="text-sm bg-gray-50 p-2 rounded">
                      <div className="font-medium">{area.name}</div>
                      <div className="text-gray-600">
                        {Math.round(area.width)} × {Math.round(area.height)} px
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateGallery;
