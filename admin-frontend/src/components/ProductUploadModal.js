import React, { useState, useEffect } from 'react';
import { useApi } from '../hooks/useApi';
import { useSSEProgress } from '../hooks/useSSEProgress';
import { useProgressSimulation } from '../hooks/useProgressSimulation';

const ProductUploadModal = ({ isOpen, onClose, onUpload, onUploadComplete }) => {
  const api = useApi();
  const [templates, setTemplates] = useState([]);
  const [loading, setLoading] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState(null);
  const [uploading, setUploading] = useState(false);

  // SSE Progress tracking
  const {
    sessionId,
    progress: rawProgress,
    isConnected,
    error: progressError,
    startProgressSession,
    connectToProgressStream,
    disconnectFromProgressStream,
    resetProgress,
  } = useSSEProgress();

  // Smooth progress simulation
  const progress = useProgressSimulation(rawProgress, uploading && isConnected);

  // Enhanced logging and progress state
  const [logs, setLogs] = useState([]);
  const [showLogs, setShowLogs] = useState(false);
  const [detailedProgress, setDetailedProgress] = useState({
    currentFile: '',
    filesProcessed: 0,
    totalFiles: 0,
    currentOperation: '',
    warnings: [],
    errors: [],
  });

  // Define upload steps for progress tracking
  const uploadSteps = [
    'Checking for duplicates',
    'Processing and formatting images',
    'Creating product mockups',
    'Uploading to Etsy store',
  ];
  const [stage, setStage] = useState('template'); // 'template', 'mockup', 'canvas', 'size', 'format', 'upload'
  const [canvasConfigs, setCanvasConfigs] = useState([]);
  const [selectedCanvasConfig, setSelectedCanvasConfig] = useState(null);
  const [sizeConfigs, setSizeConfigs] = useState([]);
  const [selectedSizeConfig, setSelectedSizeConfig] = useState(null);
  const [mockups, setMockups] = useState([]);
  const [selectedMockup, setSelectedMockup] = useState(null);
  const [loadingMockups, setLoadingMockups] = useState(false);
  const [selectedFormats, setSelectedFormats] = useState(['png']); // Default to PNG, can include 'svg', 'psd'

  // Helper functions for enhanced logging
  const addLog = (type, message, details = null) => {
    const timestamp = new Date().toLocaleTimeString();
    const logEntry = {
      id: Date.now() + Math.random(),
      timestamp,
      type, // 'info', 'success', 'warning', 'error'
      message,
      details,
    };
    setLogs(prev => [...prev, logEntry]);
    console.log(`[${type.toUpperCase()}] ${message}`, details);
  };

  const updateDetailedProgress = updates => {
    setDetailedProgress(prev => ({ ...prev, ...updates }));
  };

  const resetUploadState = () => {
    setLogs([]);
    setDetailedProgress({
      currentFile: '',
      filesProcessed: 0,
      totalFiles: 0,
      currentOperation: '',
      warnings: [],
      errors: [],
    });
    setShowLogs(false);
  };

  // Auto-scroll logs to bottom
  useEffect(() => {
    if (showLogs && logs.length > 0) {
      const logsContainer = document.querySelector('.logs-container');
      if (logsContainer) {
        logsContainer.scrollTop = logsContainer.scrollHeight;
      }
    }
  }, [logs, showLogs]);

  useEffect(() => {
    if (isOpen) {
      fetchTemplates();
      resetUploadState(); // Reset upload state when modal opens
    } else {
      resetUploadState(); // Reset upload state when modal closes
    }
  }, [isOpen]); // eslint-disable-line react-hooks/exhaustive-deps

  // Monitor progress updates for enhanced logging
  useEffect(() => {
    if (rawProgress && uploading) {
      const { message, step, totalSteps, progressPercent, elapsedTime, remainingTime } = rawProgress;

      if (message) {
        // Update detailed progress based on message content
        if (message.includes('duplicate')) {
          updateDetailedProgress({ currentOperation: 'Checking for duplicates' });
        } else if (message.includes('processing') || message.includes('resize')) {
          updateDetailedProgress({ currentOperation: 'Processing and formatting images' });
        } else if (message.includes('mockup') || message.includes('generate')) {
          updateDetailedProgress({ currentOperation: 'Creating product mockups' });
        } else if (message.includes('upload') || message.includes('etsy')) {
          updateDetailedProgress({ currentOperation: 'Uploading to Etsy store' });
        }

        // Add progress log entry
        addLog('info', `Step ${step}/${totalSteps}: ${message}`, {
          progressPercent: Math.round(progressPercent || 0),
          elapsedTime: Math.round(elapsedTime || 0),
          remainingTime: Math.round(remainingTime || 0),
        });
      }
    }
  }, [rawProgress, uploading]);

  // Monitor connection status
  useEffect(() => {
    if (sessionId) {
      if (isConnected) {
        addLog('success', 'Connected to progress stream', { sessionId });
      } else if (uploading) {
        addLog('warning', 'Attempting to connect to progress stream...', { sessionId });
      }
    }
  }, [isConnected, sessionId, uploading]);

  // Monitor errors
  useEffect(() => {
    if (progressError && uploading) {
      addLog('error', `Progress tracking error: ${progressError}`);
      updateDetailedProgress({
        errors: [...detailedProgress.errors, progressError],
      });
    }
  }, [progressError, uploading, detailedProgress.errors]);

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

  const fetchCanvasConfigs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings/canvas-config');
      setCanvasConfigs(response || []);
    } catch (error) {
      console.error('Error fetching canvas configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchSizeConfigs = async () => {
    try {
      setLoading(true);
      const response = await api.get('/settings/size-config');
      setSizeConfigs(response || []);
    } catch (error) {
      console.error('Error fetching size configs:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateSelect = template => {
    setSelectedTemplate(template);
  };

  const handleMockupSelect = mockup => {
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

  const handleContinueToCanvas = () => {
    if (!selectedMockup) {
      alert('Please select a mockup first');
      return;
    }
    fetchCanvasConfigs();
    setStage('canvas');
  };

  const handleContinueToSize = () => {
    if (!selectedCanvasConfig) {
      alert('Please select a canvas configuration first');
      return;
    }
    fetchSizeConfigs();
    setStage('size');
  };

  const handleContinueToFormat = () => {
    if (!selectedSizeConfig) {
      alert('Please select a size configuration first');
      return;
    }
    setStage('format');
  };

  const handleContinueToUpload = () => {
    if (!selectedFormats || selectedFormats.length === 0) {
      alert('Please select at least one file format');
      return;
    }
    setStage('upload');
  };

  const handleBack = () => {
    switch (stage) {
      case 'mockup':
        setStage('template');
        setSelectedMockup(null);
        break;
      case 'canvas':
        setStage('mockup');
        setSelectedCanvasConfig(null);
        break;
      case 'size':
        setStage('canvas');
        setSelectedSizeConfig(null);
        break;
      case 'format':
        setStage('size');
        break;
      case 'upload':
        setStage('format');
        break;
      default:
        // No action needed for other stages
        break;
    }
  };

  const handleUpload = async () => {
    if (
      !selectedTemplate ||
      !selectedMockup ||
      !selectedCanvasConfig ||
      !selectedSizeConfig ||
      !selectedFormats ||
      selectedFormats.length === 0
    ) {
      alert('Please complete all configuration steps first');
      return;
    }

    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.multiple = true;
    input.onchange = async e => {
      const files = Array.from(e.target.files);
      if (files.length === 0) return;

      // Check file sizes to warn about potential timeouts
      const maxFileSize = 50 * 1024 * 1024; // 50MB limit
      const totalSize = files.reduce((sum, file) => sum + file.size, 0);
      const largeFiles = files.filter(file => file.size > maxFileSize);

      if (largeFiles.length > 0) {
        const fileNames = largeFiles.map(f => f.name).join(', ');
        if (
          !window.confirm(
            `Warning: Some files are very large (${fileNames}). This may cause upload timeouts. Continue anyway?`
          )
        ) {
          return;
        }
      }

      if (totalSize > 100 * 1024 * 1024) {
        // 100MB total
        if (
          !window.confirm(
            `Warning: Total upload size is ${(totalSize / 1024 / 1024).toFixed(1)}MB. This may take a long time and could timeout. Continue anyway?`
          )
        ) {
          return;
        }
      }

      // Initialize upload state
      resetUploadState();
      setUploading(true);

      // Update detailed progress with file information
      updateDetailedProgress({
        totalFiles: files.length,
        filesProcessed: 0,
        currentOperation: 'Starting upload...',
      });

      try {
        addLog('info', `Starting upload of ${files.length} files`, {
          fileNames: files.map(f => f.name),
          totalSize: `${(totalSize / 1024 / 1024).toFixed(1)}MB`,
        });

        // Start SSE progress session with file information
        addLog('info', 'Initializing progress tracking...');
        const sessionData = await startProgressSession(files);
        connectToProgressStream(sessionData.sessionId);

        addLog('success', 'Progress tracking initialized', {
          sessionId: sessionData.sessionId,
          estimatedTime: `${sessionData.estimated_time}s`,
        });

        // First, save the design information
        const designData = {
          product_template_id: selectedTemplate.id,
          mockup_id: selectedMockup.id,
          starting_name: selectedMockup.starting_name,
          canvas_config_id: selectedCanvasConfig.id,
          size_config_id: selectedSizeConfig.id,
          is_digital: false,
          file_formats: selectedFormats, // Include selected file formats
        };

        // Then proceed with file upload with session ID for progress tracking
        const uploadFormData = new FormData();
        files.forEach(file => {
          uploadFormData.append('files', file);
        });
        uploadFormData.append('design_data', JSON.stringify(designData));
        uploadFormData.append('session_id', sessionData.sessionId);

        // Upload files with detailed logging
        addLog('info', 'Uploading design files...', { fileCount: files.length });
        updateDetailedProgress({ currentOperation: 'Uploading design files...' });

        const designResponse = await api.postFormDataWithRetry('/designs/', uploadFormData);

        // Check if any designs were created
        const uploadedCount = files.length;
        const createdCount = designResponse.designs?.length || 0;
        const duplicateCount = uploadedCount - createdCount;

        addLog('success', `Successfully uploaded ${createdCount} designs`, {
          designIds: designResponse.designs?.map(d => d.id) || [],
          duplicatesSkipped: duplicateCount,
        });

        // Handle case where all images were duplicates
        if (!designResponse.designs || designResponse.designs.length === 0) {
          console.warn('⚠️ No new designs created - all images were duplicates');

          const duplicateMessage =
            uploadedCount === 1
              ? 'The uploaded image was a duplicate. No new design was created.'
              : `All ${uploadedCount} uploaded images were duplicates. No new designs were created.`;

          addLog('warning', duplicateMessage, {
            uploadedCount,
            duplicatesSkipped: uploadedCount,
          });

          updateDetailedProgress({
            filesProcessed: files.length,
            currentOperation: 'Upload completed - duplicates detected',
          });

          alert(duplicateMessage);

          if (onUploadComplete) {
            onUploadComplete();
          } else if (onUpload) {
            onUpload();
          }
          onClose();
          return; // Stop here - don't attempt mockup upload
        }

        // Log if some duplicates were skipped
        if (duplicateCount > 0) {
          console.warn(`⚠️ Skipped ${duplicateCount} duplicate image(s)`);
          addLog('info', `${createdCount} design(s) created (${duplicateCount} duplicate(s) skipped)`, {
            created: createdCount,
            duplicates: duplicateCount,
          });
        }

        const productData = {
          product_template_id: selectedTemplate.id,
          mockup_id: selectedMockup.id,
          design_ids: [],
        };
        const mockupFormData = new FormData();
        designResponse.designs.forEach(design => {
          productData.design_ids.push(design.id);
        });

        mockupFormData.append('product_data', JSON.stringify(productData));

        addLog('info', `Creating product mockups for ${createdCount} design(s)...`, {
          templateId: selectedTemplate.id,
          mockupId: selectedMockup.id,
          designCount: createdCount,
        });
        updateDetailedProgress({ currentOperation: 'Creating product mockups...' });

        const result = await api.postFormDataWithRetry('/mockups/upload-mockup', mockupFormData);

        addLog('success', 'Mockup generation completed', {
          result: result.result?.message || 'Mockups created successfully',
        });

        let successMessage = `Successfully created ${createdCount} design(s)!`;
        if (duplicateCount > 0) {
          successMessage += `\n(${duplicateCount} duplicate(s) skipped)`;
        }
        if (result.result?.digital_message) {
          successMessage += `\n\n${result.result.digital_message}`;
        }
        if (result.result?.message) {
          successMessage += `\n${result.result.message}`;
        }

        // Log final success
        addLog('success', 'Upload process completed successfully!', {
          createdCount,
          duplicatesSkipped: duplicateCount,
          digitalMessage: result.result?.digital_message,
          finalMessage: result.result?.message,
        });

        updateDetailedProgress({
          filesProcessed: files.length,
          currentOperation: 'Upload completed',
        });

        alert(successMessage);

        if (onUploadComplete) {
          onUploadComplete();
        } else if (onUpload) {
          onUpload();
        }
        onClose();
      } catch (err) {
        console.error('Upload error:', err);

        // Log detailed error information
        addLog('error', 'Upload failed', {
          error: err.message,
          stack: err.stack,
          timestamp: new Date().toISOString(),
        });

        updateDetailedProgress({
          currentOperation: 'Upload failed',
          errors: [...detailedProgress.errors, err.message],
        });

        // Provide specific feedback for different types of errors
        let errorMessage = err.message || 'Unknown error';
        if (err.message && err.message.includes('ERR_CONNECTION_RESET')) {
          errorMessage =
            "Connection was reset during upload. The upload may have completed successfully on the server, but we couldn't confirm it. Please check your designs list to see if the upload succeeded, or try uploading again.";
          addLog('warning', 'Connection reset detected - upload may have completed', {
            recommendation: 'Check designs list to verify upload status',
          });
        } else if (err.message && err.message.includes('Failed to fetch')) {
          errorMessage = 'Network error during upload. Please check your internet connection and try again.';
          addLog('error', 'Network connectivity issue detected');
        }

        alert(`Upload failed: ${errorMessage}`);
      } finally {
        setUploading(false);
        disconnectFromProgressStream();
        // Reset progress after a short delay to allow final updates
        setTimeout(() => {
          resetProgress();
        }, 2000);
      }
    };
    input.click();
  };

  const renderMockupSelection = () => (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">Select a mockup to use with your template:</p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {mockups.map(mockup => (
          <div
            key={mockup.id}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedMockup?.id === mockup.id ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => handleMockupSelect(mockup)}
          >
            {mockup.preview_url && (
              <img src={mockup.preview_url} alt={mockup.name} className="w-full h-40 object-cover mb-2 rounded" />
            )}
            <h3 className="font-semibold text-gray-900">{mockup.name}</h3>
            <p className="text-sm text-gray-600">{mockup.description}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const renderCanvasSelection = () => (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">Select a canvas configuration:</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {canvasConfigs.map(config => (
          <div
            key={config.id}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedCanvasConfig?.id === config.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedCanvasConfig(config)}
          >
            <h3 className="font-semibold text-gray-900">{config.name}</h3>
            <p className="text-sm text-gray-600">{config.description}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const renderSizeSelection = () => (
    <div className="space-y-4">
      <p className="text-gray-600 mb-4">Select a size configuration:</p>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 max-h-96 overflow-y-auto">
        {sizeConfigs.map(config => (
          <div
            key={config.id}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedSizeConfig?.id === config.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
            onClick={() => setSelectedSizeConfig(config)}
          >
            <h3 className="font-semibold text-gray-900">{config.name}</h3>
            <p className="text-sm text-gray-600">{config.dimensions}</p>
          </div>
        ))}
      </div>
    </div>
  );

  const toggleFormat = format => {
    if (selectedFormats.includes(format)) {
      // Don't allow deselecting if it's the only one
      if (selectedFormats.length > 1) {
        setSelectedFormats(selectedFormats.filter(f => f !== format));
      }
    } else {
      setSelectedFormats([...selectedFormats, format]);
    }
  };

  const renderFormatSelection = () => (
    <div className="space-y-4">
      <div>
        <h3 className="text-lg font-semibold text-gray-900 mb-2">Select Output File Formats</h3>
        <p className="text-gray-600 mb-4">
          Choose which file formats you want for your printfiles. You can select multiple formats.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* PNG Format */}
        <div
          className={`border rounded-lg p-6 cursor-pointer transition-all ${
            selectedFormats.includes('png')
              ? 'border-blue-500 bg-blue-50 ring-2 ring-blue-200'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => toggleFormat('png')}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <svg className="w-8 h-8 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                />
              </svg>
              <h4 className="font-semibold text-gray-900">PNG</h4>
            </div>
            {selectedFormats.includes('png') && (
              <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-2">Standard raster image format</p>
          <ul className="text-xs text-gray-500 space-y-1">
            <li>• High quality mockups</li>
            <li>• Etsy listing images</li>
            <li>• Print-ready files</li>
          </ul>
        </div>

        {/* SVG Format */}
        <div
          className={`border rounded-lg p-6 cursor-pointer transition-all ${
            selectedFormats.includes('svg')
              ? 'border-green-500 bg-green-50 ring-2 ring-green-200'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => toggleFormat('svg')}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"
                />
              </svg>
              <h4 className="font-semibold text-gray-900">SVG</h4>
            </div>
            {selectedFormats.includes('svg') && (
              <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-2">Scalable vector format</p>
          <ul className="text-xs text-gray-500 space-y-1">
            <li>• Infinitely scalable</li>
            <li>• Small file size</li>
            <li>• Ideal for cutting machines</li>
          </ul>
        </div>

        {/* PSD Format */}
        <div
          className={`border rounded-lg p-6 cursor-pointer transition-all ${
            selectedFormats.includes('psd')
              ? 'border-purple-500 bg-purple-50 ring-2 ring-purple-200'
              : 'border-gray-200 hover:border-gray-300'
          }`}
          onClick={() => toggleFormat('psd')}
        >
          <div className="flex items-center justify-between mb-3">
            <div className="flex items-center space-x-2">
              <svg className="w-8 h-8 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z"
                />
              </svg>
              <h4 className="font-semibold text-gray-900">PSD</h4>
            </div>
            {selectedFormats.includes('psd') && (
              <svg className="w-5 h-5 text-purple-500" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
            )}
          </div>
          <p className="text-sm text-gray-600 mb-2">Photoshop format</p>
          <ul className="text-xs text-gray-500 space-y-1">
            <li>• Editable layers</li>
            <li>• Professional editing</li>
            <li>• Full color control</li>
          </ul>
        </div>
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mt-4">
        <div className="flex items-start space-x-3">
          <svg className="w-5 h-5 text-blue-500 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path
              fillRule="evenodd"
              d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
              clipRule="evenodd"
            />
          </svg>
          <div className="flex-1">
            <h4 className="text-sm font-semibold text-blue-900 mb-1">Selected Formats</h4>
            <p className="text-sm text-blue-700">
              {selectedFormats.length === 0
                ? 'No formats selected'
                : selectedFormats.length === 1
                  ? `${selectedFormats[0].toUpperCase()} only`
                  : selectedFormats.map(f => f.toUpperCase()).join(', ')}
            </p>
          </div>
        </div>
      </div>
    </div>
  );

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 mt-0">
      <div
        className={`bg-white rounded-lg p-6 w-full overflow-y-auto transition-all duration-300 ${
          showLogs && uploading ? 'max-w-4xl max-h-[95vh]' : 'max-w-2xl max-h-[90vh]'
        }`}
      >
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">
            {stage === 'template'
              ? 'Select Template'
              : stage === 'mockup'
                ? 'Select Mockup'
                : stage === 'canvas'
                  ? 'Select Canvas Configuration'
                  : stage === 'size'
                    ? 'Select Size Configuration'
                    : stage === 'format'
                      ? 'Select File Formats'
                      : 'Upload Products'}
          </h2>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600">
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
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={1}
                            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                          />
                        </svg>
                      </div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">No templates found</h3>
                      <p className="text-gray-600">Create a template in your Account settings first.</p>
                    </div>
                  ) : (
                    templates.map(template => (
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
                          <h3 className="font-semibold text-gray-900">{template.template_title || template.name}</h3>
                          {selectedTemplate?.id === template.id && (
                            <svg className="w-5 h-5 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                              <path
                                fillRule="evenodd"
                                d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                                clipRule="evenodd"
                              />
                            </svg>
                          )}
                        </div>

                        <p className="text-sm text-gray-600 mb-2">{template.title || 'No listing title set'}</p>

                        {template.template_title && <p className="text-xs text-gray-500 mb-2">Key: {template.name}</p>}

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
            ) : stage === 'mockup' ? (
              renderMockupSelection()
            ) : stage === 'canvas' ? (
              renderCanvasSelection()
            ) : stage === 'size' ? (
              renderSizeSelection()
            ) : stage === 'format' ? (
              renderFormatSelection()
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">Click "Upload Images" to select and upload your designs</p>
              </div>
            )}
            {/* Action Buttons */}
            <div className="flex justify-end space-x-4 pt-6 border-t">
              {(stage === 'mockup' ||
                stage === 'canvas' ||
                stage === 'size' ||
                stage === 'format' ||
                stage === 'upload') && (
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
                onClick={
                  stage === 'template'
                    ? handleContinueToMockups
                    : stage === 'mockup'
                      ? handleContinueToCanvas
                      : stage === 'canvas'
                        ? handleContinueToSize
                        : stage === 'size'
                          ? handleContinueToFormat
                          : stage === 'format'
                            ? handleContinueToUpload
                            : handleUpload
                }
                disabled={
                  (stage === 'template' && !selectedTemplate) ||
                  (stage === 'mockup' && !selectedMockup) ||
                  (stage === 'canvas' && !selectedCanvasConfig) ||
                  (stage === 'size' && !selectedSizeConfig) ||
                  (stage === 'format' && (!selectedFormats || selectedFormats.length === 0)) ||
                  (stage === 'upload' && uploading)
                }
                className={`px-6 py-2 rounded-lg font-medium transition-colors ${
                  (
                    stage === 'template'
                      ? !selectedTemplate
                      : stage === 'mockup'
                        ? !selectedMockup
                        : stage === 'canvas'
                          ? !selectedCanvasConfig
                          : !selectedSizeConfig || uploading
                  )
                    ? 'bg-gray-400 text-white cursor-not-allowed'
                    : 'bg-blue-500 text-white hover:bg-blue-600'
                }`}
              >
                {uploading ? (
                  <div className="flex flex-col items-center w-full">
                    {/* Enhanced status header with logs toggle */}
                    <div className="w-full mb-4">
                      <div className="flex justify-between items-center mb-2">
                        <div className="flex items-center text-sm">
                          {sessionId && (
                            <>
                              <div
                                className={`w-2 h-2 rounded-full mr-2 ${isConnected ? 'bg-green-500' : 'bg-yellow-500'}`}
                              ></div>
                              <span className="text-gray-600">
                                {isConnected ? 'Connected to progress stream' : 'Connecting...'}
                              </span>
                            </>
                          )}
                        </div>
                        <button
                          onClick={() => setShowLogs(!showLogs)}
                          className="text-xs px-2 py-1 bg-gray-100 hover:bg-gray-200 rounded transition-colors"
                        >
                          {showLogs ? 'Hide Logs' : 'Show Logs'}
                        </button>
                      </div>

                      {/* Detailed progress info */}
                      <div className="text-xs text-gray-600 bg-gray-50 p-2 rounded">
                        <div className="grid grid-cols-2 gap-2">
                          <div>
                            Files: {detailedProgress.filesProcessed}/{detailedProgress.totalFiles}
                          </div>
                          <div>Operation: {detailedProgress.currentOperation || 'Initializing...'}</div>
                        </div>
                        {detailedProgress.currentFile && (
                          <div className="mt-1 truncate">Current: {detailedProgress.currentFile}</div>
                        )}
                      </div>
                    </div>

                    {/* Step indicators */}
                    <div className="flex justify-between w-full mb-3 text-xs">
                      {uploadSteps.map((step, index) => (
                        <div
                          key={index}
                          className={`flex-1 text-center px-1 ${
                            index < progress.step
                              ? 'text-blue-600 font-medium'
                              : index === progress.step - 1
                                ? 'text-blue-500 font-medium'
                                : 'text-gray-400'
                          }`}
                        >
                          <div
                            className={`w-6 h-6 rounded-full mx-auto mb-1 flex items-center justify-center text-xs ${
                              index < progress.step
                                ? 'bg-blue-600 text-white'
                                : index === progress.step - 1
                                  ? 'bg-blue-500 text-white'
                                  : 'bg-gray-200 text-gray-500'
                            }`}
                          >
                            {index + 1}
                          </div>
                          <div className="leading-tight">{step}</div>
                        </div>
                      ))}
                    </div>

                    {/* Progress message and timing */}
                    <div className="text-sm mb-2 text-center">
                      <div className="font-medium text-gray-900">{progress.message || 'Starting upload...'}</div>
                      <div className="flex justify-center items-center space-x-4 text-xs text-gray-500 mt-1">
                        {progress.elapsedTime > 0 && <span>Elapsed: {Math.round(progress.elapsedTime)}s</span>}
                        {progress.remainingTime > 0 && <span>ETA: {Math.round(progress.remainingTime)}s</span>}
                        {progress.estimatedTotalTime > 0 && (
                          <span>Total Est: {Math.round(progress.estimatedTotalTime)}s</span>
                        )}
                      </div>
                    </div>

                    <div className="w-64 bg-gray-200 rounded-full h-3 relative overflow-hidden">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-600 h-3 rounded-full transition-all duration-500 ease-out relative"
                        style={{ width: `${progress.progressPercent || 0}%` }}
                      >
                        {/* Animated shimmer effect */}
                        <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/30 to-transparent animate-pulse"></div>
                      </div>
                    </div>

                    <div className="flex justify-between items-center text-xs text-gray-600 mt-2">
                      <span>
                        Step {progress.step || 1} of {progress.totalSteps || 4}
                      </span>
                      <span className="font-medium">{Math.round(progress.progressPercent || 0)}%</span>
                    </div>

                    {/* Logs display */}
                    {showLogs && (
                      <div className="w-full mt-4 max-h-48 overflow-y-auto bg-gray-900 text-green-400 p-3 rounded text-xs font-mono logs-container">
                        <div className="flex justify-between items-center mb-2 text-gray-300">
                          <span className="font-semibold">Upload Logs ({logs.length})</span>
                          <button
                            onClick={() => setLogs([])}
                            className="text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded"
                          >
                            Clear
                          </button>
                        </div>
                        {logs.length === 0 ? (
                          <div className="text-gray-500">No logs yet...</div>
                        ) : (
                          <div className="space-y-1">
                            {logs.map(log => (
                              <div
                                key={log.id}
                                className={`flex items-start space-x-2 ${
                                  log.type === 'error'
                                    ? 'text-red-400'
                                    : log.type === 'warning'
                                      ? 'text-yellow-400'
                                      : log.type === 'success'
                                        ? 'text-green-400'
                                        : 'text-blue-400'
                                }`}
                              >
                                <span className="text-gray-500 min-w-0">[{log.timestamp}]</span>
                                <span
                                  className={`inline-block w-1 h-1 rounded-full mt-2 ${
                                    log.type === 'error'
                                      ? 'bg-red-400'
                                      : log.type === 'warning'
                                        ? 'bg-yellow-400'
                                        : log.type === 'success'
                                          ? 'bg-green-400'
                                          : 'bg-blue-400'
                                  }`}
                                ></span>
                                <div className="flex-1 min-w-0">
                                  <div className="break-words">{log.message}</div>
                                  {log.details && (
                                    <div className="text-gray-500 mt-1 pl-2 border-l border-gray-700">
                                      {typeof log.details === 'string'
                                        ? log.details
                                        : JSON.stringify(log.details, null, 2)}
                                    </div>
                                  )}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}

                    {/* Error display */}
                    {progressError && (
                      <div className="text-xs text-red-600 mt-2">Progress tracking error: {progressError}</div>
                    )}

                    {/* Errors and warnings summary */}
                    {(detailedProgress.errors.length > 0 || detailedProgress.warnings.length > 0) && !showLogs && (
                      <div className="w-full mt-2 text-xs">
                        {detailedProgress.errors.length > 0 && (
                          <div className="text-red-600">
                            ⚠️ {detailedProgress.errors.length} error(s) - Click "Show Logs" for details
                          </div>
                        )}
                        {detailedProgress.warnings.length > 0 && (
                          <div className="text-yellow-600">
                            ⚠️ {detailedProgress.warnings.length} warning(s) - Click "Show Logs" for details
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                ) : stage === 'template' ? (
                  'Continue'
                ) : stage === 'mockup' ? (
                  'Continue to Canvas'
                ) : stage === 'canvas' ? (
                  'Continue to Size'
                ) : stage === 'size' ? (
                  'Continue to Format Selection'
                ) : stage === 'format' ? (
                  'Continue to Upload'
                ) : (
                  'Upload Images'
                )}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ProductUploadModal;
