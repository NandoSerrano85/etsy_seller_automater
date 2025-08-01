import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const TemplateSelectionModal = ({ isOpen, onClose, onTemplateSelected, onUpload, onUploadComplete }) => {
  const api = useApi();
  const [templates, setTemplates] = useState([]);
  const [formData, setFormData] = useState([])
  const [loading, setLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [stage, setStage] = useState('template'); // 'template' or 'mockup'
  const [mockups, setMockups] = useState([]);
  const [selectedMockup, setSelectedMockup] = useState(null);
  const [loadingMockups, setLoadingMockups] = useState(false);

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
    }
  }, [isOpen]);

  const fetchTemplates = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings/product-template');
      setTemplates(response);
    } catch (error) {
      console.error('Error fetching templates:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchMockups = async () => {
    try {
      setLoadingMockups(true);
      const response = await api.get('/mockups/');
      setMockups(response.mockups || []);
    } catch (error) {
      console.error('Error fetching mockups:', error);
    } finally {
      setLoadingMockups(false);
    }
  };

  const handleTemplateSelect = (template) => {
    setSelectedTemplate(template);
  };

  const handleMockupSelect = (mockup) => {
    setSelectedMockup(mockup);
  };

  const handleContinueToMockups = () => {
    if (!selectedTemplate) {
      alert('Please select a template first');
      return;
    }
    fetchMockups();
    setStage('mockup');
  };

  const handleBack = () => {
    setStage('template');
    setSelectedMockup(null);
  };

  const handleUpload = async () => {
    if (!selectedTemplate || !selectedMockup) {
      alert('Please select both a template and mockup');
      return;
    }

    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = async (e) => {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;
      
      setUploading(true);
      try {
        // Create FormData object
        const formData = new FormData();
        
        // Append each file to the FormData
        files.forEach((file) => {
          formData.append('files', file);
        });

        // Add template name to FormData
        formData.append('template_name', selectedTemplate.name);
        formData.append('mockup_id', selectedMockup.id);
        console.log(formData);
        const result = await api.postFormData('/mockups/upload-mockup', formData, {
          headers: {
            'Content-Type': 'multipart/form-data',
          }
        });
        
        let successMessage = 'Files uploaded successfully!';
        if (result.result?.digital_message) {
          successMessage += `\n\n${result.result.digital_message}`;
        }
        if (result.result?.message) {
          successMessage += `\n${result.result.message}`;
        }
        
        alert(successMessage);
        
        if (onUploadComplete) {
          onUploadComplete();
        } else if (onUpload) {
          onUpload();
        }
        onClose();
      } catch (err) {
        console.error('Upload error:', err);
        alert(`Upload failed: ${err.message || 'Unknown error'}`);
      } finally {
        setUploading(false);
      }
    };
    input.click();
  };

  const renderMockupSelection = () => (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">
        Select a mockup to use with your template:
      </p>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {mockups.map((mockup) => (
          <div
            key={mockup.id}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedMockup?.id === mockup.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleMockupSelect(mockup)}
          >
            {mockup.preview_url && (
              <img 
                src={mockup.preview_url} 
                alt={mockup.name}
                className="w-full h-40 object-cover mb-2 rounded"
              />
            )}
            <h3 className="font-semibold text-gray-900">{mockup.name}</h3>
            <p className="text-sm text-gray-600">{mockup.description}</p>
          </div>
        ))}
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 mt-0">
      <div className="bg-white rounded-lg p-6 w-full max-w-2xl max-h-[90vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            {stage === 'template' ? 'Select Template' : 'Select Mockup'}
          </h2>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {loading || loadingMockups ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <p className="text-gray-600">Loading...</p>
          </div>
        ) : (
          <>
          {stage === 'template' ? (
            <div className="space-y-4">
            <p className="text-gray-600 mb-4">
              Select a template to use for creating Etsy listings from your uploaded images:
            </p>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
              {templates.length === 0 ? (
                <div className="col-span-full text-center py-8">
                  <div className="text-gray-400 mb-4">
                    <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-2">No templates found</h3>
                  <p className="text-gray-600">Create a template in your Account settings first.</p>
                </div>
              ) : (
                templates.map((template) => (
                  <div
                    key={template.id}
                    className={`border rounded-lg p-4 cursor-pointer transition-all ${
                      selectedTemplate?.id === template.id
                        ? 'border-blue-500 bg-blue-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => handleTemplateSelect(template)}
                  >
                    <div className="flex justify-between items-start mb-2">
                      <h3 className="font-semibold text-gray-900">
                        {template.template_title || template.name}
                      </h3>
                      {selectedTemplate?.id === template.id && (
                        <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      )}
                    </div>
                    
                    <p className="text-sm text-gray-600 mb-2">
                      {template.title || 'No listing title set'}
                    </p>
                    
                    {template.template_title && (
                      <p className="text-xs text-gray-500 mb-2">
                        Key: {template.name}
                      </p>
                    )}
                    
                    <div className="space-y-1 text-xs text-gray-500">
                      <div className="flex justify-between">
                        <span>Price:</span>
                        <span className="font-medium">${template.price || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Quantity:</span>
                        <span className="font-medium">{template.quantity || 0}</span>
                      </div>
                      <div className="flex justify-between">
                        <span>Type:</span>
                        <span className="font-medium capitalize">{template.type || 'N/A'}</span>
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
          ) : (
            renderMockupSelection()
          )}
          {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t">
              {stage === 'mockup' && (
                <button
                  type="button"
                  onClick={handleBack}
                  className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  Back
                </button>
              )}
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 text-gray-700 bg-gray-200 rounded-lg hover:bg-gray-300 transition-colors"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={stage === 'template' ? handleContinueToMockups : handleUpload}
                disabled={stage === 'template' ? !selectedTemplate : (!selectedMockup || uploading)}
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  (stage === 'template' ? !selectedTemplate : (!selectedMockup || uploading))
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {uploading ? 'Uploading...' : stage === 'template' ? 'Continue' : 'Upload Images'}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default TemplateSelectionModal; 