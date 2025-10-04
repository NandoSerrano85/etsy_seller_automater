import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import printerService from '../services/printerService';
import { useNotifications } from './NotificationSystem';

const TemplateSelector = ({ printerId, currentTemplateIds = [], onTemplatesUpdated, onClose }) => {
  const [availableTemplates, setAvailableTemplates] = useState([]);
  const [selectedTemplates, setSelectedTemplates] = useState(new Set(currentTemplateIds));
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const { addNotification } = useNotifications();
  const api = useApi();

  useEffect(() => {
    loadTemplates();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const loadTemplates = async () => {
    setLoading(true);
    try {
      const response = await api.get('/settings/product-template');
      setAvailableTemplates(response || []);
    } catch (error) {
      console.error('Error fetching templates:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load templates',
      });
      setAvailableTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const toggleTemplate = templateId => {
    const newSelected = new Set(selectedTemplates);
    if (newSelected.has(templateId)) {
      newSelected.delete(templateId);
    } else {
      newSelected.add(templateId);
    }
    setSelectedTemplates(newSelected);
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      const currentSet = new Set(currentTemplateIds);
      const selectedSet = selectedTemplates;

      // Templates to add (in selected but not in current)
      const toAdd = [...selectedSet].filter(id => !currentSet.has(id));

      // Templates to remove (in current but not in selected)
      const toRemove = [...currentSet].filter(id => !selectedSet.has(id));

      // Add templates
      for (const templateId of toAdd) {
        const result = await printerService.addTemplateToPrinter(printerId, templateId);
        if (!result.success) {
          throw new Error(`Failed to add template: ${result.error}`);
        }
      }

      // Remove templates
      for (const templateId of toRemove) {
        const result = await printerService.removeTemplateFromPrinter(printerId, templateId);
        if (!result.success) {
          throw new Error(`Failed to remove template: ${result.error}`);
        }
      }

      addNotification({
        type: 'success',
        message: 'Templates updated successfully',
      });

      onTemplatesUpdated();
      onClose();
    } catch (error) {
      addNotification({
        type: 'error',
        message: error.message || 'Failed to update templates',
      });
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={onClose} />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-2xl max-h-[80vh] flex flex-col">
          <div className="p-6 border-b border-sage-200">
            <div className="flex items-center justify-between">
              <h2 className="text-xl font-semibold text-sage-900">Select Supported Templates</h2>
              <button
                onClick={onClose}
                disabled={saving}
                className="text-sage-400 hover:text-sage-600 transition-colors disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-6">
            {loading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map(i => (
                  <div key={i} className="h-16 bg-sage-100 rounded-lg animate-pulse"></div>
                ))}
              </div>
            ) : availableTemplates.length === 0 ? (
              <div className="text-center py-12">
                <div className="text-sage-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-lg font-medium text-sage-900 mb-2">No Templates Found</h3>
                <p className="text-sage-600">Create some templates first to associate them with this printer.</p>
              </div>
            ) : (
              <div className="space-y-2">
                {availableTemplates.map(template => (
                  <div
                    key={template.id}
                    onClick={() => toggleTemplate(template.id)}
                    className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                      selectedTemplates.has(template.id)
                        ? 'border-sage-500 bg-sage-50'
                        : 'border-sage-200 hover:border-sage-300'
                    }`}
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-colors ${
                          selectedTemplates.has(template.id)
                            ? 'bg-sage-600 border-sage-600'
                            : 'border-sage-300 bg-white'
                        }`}
                      >
                        {selectedTemplates.has(template.id) && (
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 12 12">
                            <path d="M10 3L4.5 8.5L2 6" stroke="currentColor" strokeWidth="2" fill="none" />
                          </svg>
                        )}
                      </div>

                      <div className="flex-1">
                        <h4 className="font-medium text-sage-900">{template.name}</h4>
                        {template.template_title && <p className="text-sm text-sage-500">{template.template_title}</p>}
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          <div className="p-6 border-t border-sage-200">
            <div className="flex justify-between items-center">
              <p className="text-sm text-sage-600">
                {selectedTemplates.size} template{selectedTemplates.size !== 1 ? 's' : ''} selected
              </p>
              <div className="flex space-x-3">
                <button
                  onClick={onClose}
                  disabled={saving}
                  className="px-4 py-2 text-sage-700 bg-sage-100 hover:bg-sage-200 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center space-x-2"
                >
                  {saving && (
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  )}
                  <span>{saving ? 'Saving...' : 'Save Changes'}</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default TemplateSelector;
