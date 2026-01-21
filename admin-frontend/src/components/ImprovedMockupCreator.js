import React, { useState, useEffect, useRef } from 'react';
import { useApi } from '../hooks/useApi';
import ProgressIndicator from './ProgressIndicator';

const ImprovedMockupCreator = ({ isOpen, onClose, onComplete }) => {
  const api = useApi();
  const canvasRef = useRef(null);

  // Workflow state
  const [currentStep, setCurrentStep] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  // Step data
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [watermarkFile, setWatermarkFile] = useState(null);
  const [mockupSettings, setMockupSettings] = useState({
    name: '',
    startingNumber: 100,
    quality: 'high',
  });

  // Data from API
  const [templates, setTemplates] = useState([]);

  const steps = [
    { id: 1, title: 'Choose Template', description: 'Select a product template' },
    { id: 2, title: 'Upload Files', description: 'Add your design files' },
    { id: 3, title: 'Add Watermark', description: 'Optional branding watermark' },
    { id: 4, title: 'Configure', description: 'Set mockup preferences' },
    { id: 5, title: 'Create', description: 'Generate your mockups' },
  ];

  useEffect(() => {
    if (isOpen) {
      loadTemplates();
    }
  }, [isOpen]);

  const loadTemplates = async () => {
    try {
      setIsLoading(true);
      const response = await api.get('/settings/product-template');
      setTemplates(response);
    } catch (err) {
      setError('Failed to load templates');
      console.error('Error loading templates:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNext = async () => {
    try {
      setError('');

      // Validation based on current step
      if (currentStep === 1 && !selectedTemplate) {
        setError('Please select a template');
        return;
      }

      if (currentStep === 2 && uploadedFiles.length === 0) {
        setError('Please upload at least one design file');
        return;
      }

      if (currentStep === 4 && !mockupSettings.name.trim()) {
        setError('Please enter a name for your mockup');
        return;
      }

      if (currentStep === 5) {
        await createMockup();
        return;
      }

      setCurrentStep(prev => Math.min(prev + 1, steps.length));
    } catch (err) {
      setError('An error occurred. Please try again.');
    }
  };

  const handlePrevious = () => {
    setError('');
    setCurrentStep(prev => Math.max(prev - 1, 1));
  };

  const handleFileUpload = event => {
    const files = Array.from(event.target.files);
    setUploadedFiles(files);
  };

  const handleWatermarkUpload = event => {
    const file = event.target.files[0];
    setWatermarkFile(file);
  };

  const createMockup = async () => {
    try {
      setIsLoading(true);
      setError('');

      // Create mockup group
      const mockupGroup = await api.post('/mockups/group', {
        name: mockupSettings.name,
        product_template_id: selectedTemplate.id,
        starting_name: mockupSettings.startingNumber,
      });

      // Upload files
      const formData = new FormData();
      uploadedFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('mockup_id', mockupGroup.id);
      if (watermarkFile) {
        formData.append('watermark_file', watermarkFile);
      }

      await api.postFormData('/mockups/upload', formData);

      setSuccess('Mockup created successfully!');
      setTimeout(() => {
        onComplete && onComplete();
        onClose && onClose();
      }, 2000);
    } catch (err) {
      setError('Failed to create mockup. Please try again.');
      console.error('Mockup creation error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (currentStep) {
      case 1:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Choose Your Template</h3>
              <p className="text-gray-600">Select the product template for your mockups</p>
            </div>

            {isLoading ? (
              <div className="text-center py-12">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading templates...</p>
              </div>
            ) : (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
                {templates.map(template => (
                  <div
                    key={template.id}
                    onClick={() => setSelectedTemplate(template)}
                    className={`p-4 border-2 rounded-xl cursor-pointer transition-all duration-200 hover:shadow-md ${
                      selectedTemplate?.id === template.id
                        ? 'border-blue-500 bg-blue-50 shadow-md'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-semibold text-gray-900">{template.name}</h4>
                      {selectedTemplate?.id === template.id && (
                        <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center">
                          <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                    <p className="text-sm text-gray-600 mb-3">{template.template_title || 'Product template'}</p>
                    <div className="grid grid-cols-2 gap-2 text-xs text-gray-500">
                      <span>Price: ${template.price || 0}</span>
                      <span>Type: {template.type || 'Standard'}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        );

      case 2:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Upload Your Designs</h3>
              <p className="text-gray-600">Add the design files you want to create mockups for</p>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                multiple
                accept="image/*"
                onChange={handleFileUpload}
                className="hidden"
                id="file-upload"
              />
              <label htmlFor="file-upload" className="cursor-pointer">
                <div className="space-y-4">
                  <div className="text-4xl text-gray-400">📁</div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">Click to upload files</p>
                    <p className="text-sm text-gray-500">PNG, JPG, or GIF up to 10MB each</p>
                  </div>
                </div>
              </label>
            </div>

            {uploadedFiles.length > 0 && (
              <div className="space-y-3">
                <h4 className="font-medium text-gray-900">Selected Files ({uploadedFiles.length})</h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center space-x-3 p-3 bg-gray-50 rounded-lg">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <span className="text-blue-600 font-medium text-sm">{index + 1}</span>
                      </div>
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-gray-900 truncate">{file.name}</p>
                        <p className="text-xs text-gray-500">{(file.size / 1024 / 1024).toFixed(1)} MB</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        );

      case 3:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Add Watermark (Optional)</h3>
              <p className="text-gray-600">Add a watermark to brand your mockups</p>
            </div>

            <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center hover:border-gray-400 transition-colors">
              <input
                type="file"
                accept="image/*"
                onChange={handleWatermarkUpload}
                className="hidden"
                id="watermark-upload"
              />
              <label htmlFor="watermark-upload" className="cursor-pointer">
                <div className="space-y-4">
                  <div className="text-4xl text-gray-400">🏷️</div>
                  <div>
                    <p className="text-lg font-medium text-gray-900">Click to upload watermark</p>
                    <p className="text-sm text-gray-500">PNG or JPG with transparency recommended</p>
                  </div>
                </div>
              </label>
            </div>

            {watermarkFile && (
              <div className="p-3 bg-green-50 rounded-lg border border-green-200">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-green-100 rounded-lg flex items-center justify-center">
                    <span className="text-green-600">✓</span>
                  </div>
                  <div>
                    <p className="text-sm font-medium text-green-900">{watermarkFile.name}</p>
                    <p className="text-xs text-green-700">Watermark ready</p>
                  </div>
                </div>
              </div>
            )}

            <div className="text-center">
              <button onClick={() => setCurrentStep(4)} className="text-blue-600 hover:text-blue-700 text-sm">
                Skip watermark →
              </button>
            </div>
          </div>
        );

      case 4:
        return (
          <div className="space-y-6">
            <div className="text-center">
              <h3 className="text-xl font-semibold text-gray-900 mb-2">Configure Settings</h3>
              <p className="text-gray-600">Set your mockup preferences</p>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Mockup Name</label>
                <input
                  type="text"
                  value={mockupSettings.name}
                  onChange={e => setMockupSettings(prev => ({ ...prev, name: e.target.value }))}
                  placeholder="e.g., Summer Collection Mockups"
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Starting Number</label>
                <input
                  type="number"
                  min="1"
                  value={mockupSettings.startingNumber}
                  onChange={e =>
                    setMockupSettings(prev => ({ ...prev, startingNumber: parseInt(e.target.value) || 100 }))
                  }
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-500 mt-1">Files will be numbered starting from this value</p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Output Quality</label>
                <select
                  value={mockupSettings.quality}
                  onChange={e => setMockupSettings(prev => ({ ...prev, quality: e.target.value }))}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  <option value="standard">Standard (Faster)</option>
                  <option value="high">High Quality (Recommended)</option>
                  <option value="premium">Premium (Slower)</option>
                </select>
              </div>
            </div>

            {/* Summary */}
            <div className="bg-gray-50 p-4 rounded-lg">
              <h4 className="font-medium text-gray-900 mb-3">Summary</h4>
              <div className="space-y-2 text-sm text-gray-600">
                <div className="flex justify-between">
                  <span>Template:</span>
                  <span className="font-medium">{selectedTemplate?.name}</span>
                </div>
                <div className="flex justify-between">
                  <span>Files:</span>
                  <span className="font-medium">{uploadedFiles.length} design(s)</span>
                </div>
                <div className="flex justify-between">
                  <span>Watermark:</span>
                  <span className="font-medium">{watermarkFile ? 'Yes' : 'No'}</span>
                </div>
                <div className="flex justify-between">
                  <span>Quality:</span>
                  <span className="font-medium capitalize">{mockupSettings.quality}</span>
                </div>
              </div>
            </div>
          </div>
        );

      case 5:
        return (
          <div className="space-y-6 text-center">
            <div className="text-6xl mb-4">🎨</div>
            <h3 className="text-xl font-semibold text-gray-900">Ready to Create!</h3>
            <p className="text-gray-600">
              We're ready to generate {uploadedFiles.length} professional mockup{uploadedFiles.length !== 1 ? 's' : ''}
              using your "{selectedTemplate?.name}" template.
            </p>

            {isLoading && (
              <div className="space-y-4">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
                <p className="text-gray-600">Creating your mockups...</p>
              </div>
            )}

            {success && (
              <div className="bg-green-50 p-4 rounded-lg border border-green-200">
                <p className="text-green-700 font-medium">{success}</p>
              </div>
            )}
          </div>
        );

      default:
        return null;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-bold text-gray-900">Create Mockups</h2>
            <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Progress Indicator */}
          <ProgressIndicator steps={steps} currentStep={currentStep} variant="numbered" />
        </div>

        {/* Content */}
        <div className="p-6">
          {renderStepContent()}

          {/* Error Display */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-700 text-sm">{error}</p>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-between items-center">
          <button
            onClick={handlePrevious}
            disabled={currentStep === 1}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              currentStep === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Previous
          </button>

          <div className="text-sm text-gray-500">
            Step {currentStep} of {steps.length}
          </div>

          <button
            onClick={handleNext}
            disabled={isLoading}
            className={`px-6 py-2 rounded-lg font-medium transition-colors ${
              isLoading
                ? 'bg-gray-400 text-white cursor-not-allowed'
                : currentStep === steps.length
                  ? 'bg-green-500 text-white hover:bg-green-600'
                  : 'bg-blue-500 text-white hover:bg-blue-600'
            }`}
          >
            {isLoading ? 'Creating...' : currentStep === steps.length ? 'Create Mockups' : 'Continue'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default ImprovedMockupCreator;
