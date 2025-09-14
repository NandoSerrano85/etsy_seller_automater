import React, { useState, useRef, useCallback, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from './NotificationSystem';
import {
  CloudArrowUpIcon,
  PhotoIcon,
  Square2StackIcon,
  EyeIcon,
  PlusIcon,
  TrashIcon,
  ArrowPathIcon,
  CheckIcon,
  XMarkIcon,
  CursorArrowRippleIcon,
} from '@heroicons/react/24/outline';

const TemplateEditor = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();

  // State management
  const [loading, setLoading] = useState(false);
  const [backgroundImage, setBackgroundImage] = useState(null);
  const [backgroundFile, setBackgroundFile] = useState(null);
  const [designAreas, setDesignAreas] = useState([]);
  const [selectedArea, setSelectedArea] = useState(null);
  const [isDrawing, setIsDrawing] = useState(false);
  const [drawStart, setDrawStart] = useState(null);
  const [templateData, setTemplateData] = useState({
    name: '',
    description: '',
    category: '',
  });
  const [previewMode, setPreviewMode] = useState(false);
  const [previewImage, setPreviewImage] = useState(null);

  // Refs
  const canvasRef = useRef(null);
  const fileInputRef = useRef(null);
  const imageRef = useRef(null);

  // Canvas drawing state
  const [canvasSize, setCanvasSize] = useState({ width: 800, height: 600 });
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [imageOffset, setImageOffset] = useState({ x: 0, y: 0 });
  const [scale, setScale] = useState(1);

  // Initialize canvas when background image changes
  useEffect(() => {
    if (backgroundImage && imageRef.current) {
      const img = imageRef.current;
      const canvas = canvasRef.current;

      const updateCanvasSize = () => {
        const containerWidth = canvas.parentElement.clientWidth - 40; // Account for padding
        const maxHeight = 600;

        const imgAspectRatio = img.naturalWidth / img.naturalHeight;
        let newWidth = Math.min(containerWidth, img.naturalWidth);
        let newHeight = newWidth / imgAspectRatio;

        if (newHeight > maxHeight) {
          newHeight = maxHeight;
          newWidth = newHeight * imgAspectRatio;
        }

        setImageSize({ width: newWidth, height: newHeight });
        setCanvasSize({ width: newWidth, height: newHeight });
        setScale(newWidth / img.naturalWidth);

        // Center the image
        setImageOffset({ x: 0, y: 0 });
      };

      if (img.complete) {
        updateCanvasSize();
      } else {
        img.onload = updateCanvasSize;
      }
    }
  }, [backgroundImage]);

  // Redraw canvas when design areas or canvas size changes
  useEffect(() => {
    drawCanvas();
  }, [designAreas, selectedArea, canvasSize, backgroundImage]);

  const handleBackgroundUpload = event => {
    const file = event.target.files[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      addNotification('Please select a valid image file', 'error');
      return;
    }

    setBackgroundFile(file);
    const reader = new FileReader();
    reader.onload = e => {
      setBackgroundImage(e.target.result);
      setDesignAreas([]); // Reset design areas when new background is uploaded
    };
    reader.readAsDataURL(file);
  };

  const drawCanvas = () => {
    const canvas = canvasRef.current;
    if (!canvas || !backgroundImage) return;

    const ctx = canvas.getContext('2d');
    canvas.width = canvasSize.width;
    canvas.height = canvasSize.height;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background image
    if (imageRef.current && imageRef.current.complete) {
      ctx.drawImage(imageRef.current, imageOffset.x, imageOffset.y, imageSize.width, imageSize.height);
    }

    // Draw design areas
    designAreas.forEach((area, index) => {
      const isSelected = selectedArea === index;

      // Scale coordinates
      const scaledArea = {
        x: area.x * scale,
        y: area.y * scale,
        width: area.width * scale,
        height: area.height * scale,
      };

      // Draw area rectangle
      ctx.strokeStyle = isSelected ? '#3b82f6' : '#ef4444';
      ctx.lineWidth = isSelected ? 3 : 2;
      ctx.setLineDash(isSelected ? [] : [5, 5]);
      ctx.strokeRect(scaledArea.x, scaledArea.y, scaledArea.width, scaledArea.height);

      // Fill with semi-transparent color
      ctx.fillStyle = isSelected ? 'rgba(59, 130, 246, 0.2)' : 'rgba(239, 68, 68, 0.1)';
      ctx.fillRect(scaledArea.x, scaledArea.y, scaledArea.width, scaledArea.height);

      // Draw area label
      ctx.fillStyle = isSelected ? '#1d4ed8' : '#dc2626';
      ctx.font = '14px Arial';
      ctx.fillText(area.name || `Area ${index + 1}`, scaledArea.x + 5, scaledArea.y + 20);

      // Draw resize handles if selected
      if (isSelected) {
        const handleSize = 8;
        ctx.fillStyle = '#3b82f6';

        // Corner handles
        const handles = [
          { x: scaledArea.x - handleSize / 2, y: scaledArea.y - handleSize / 2 }, // Top-left
          { x: scaledArea.x + scaledArea.width - handleSize / 2, y: scaledArea.y - handleSize / 2 }, // Top-right
          { x: scaledArea.x - handleSize / 2, y: scaledArea.y + scaledArea.height - handleSize / 2 }, // Bottom-left
          { x: scaledArea.x + scaledArea.width - handleSize / 2, y: scaledArea.y + scaledArea.height - handleSize / 2 }, // Bottom-right
        ];

        handles.forEach(handle => {
          ctx.fillRect(handle.x, handle.y, handleSize, handleSize);
        });
      }
    });

    ctx.setLineDash([]); // Reset line dash
  };

  const getCanvasCoordinates = event => {
    const canvas = canvasRef.current;
    const rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) / scale,
      y: (event.clientY - rect.top) / scale,
    };
  };

  const handleCanvasMouseDown = event => {
    if (!backgroundImage) return;

    const coords = getCanvasCoordinates(event);

    // Check if clicking on existing area
    const clickedAreaIndex = designAreas.findIndex(
      area =>
        coords.x >= area.x && coords.x <= area.x + area.width && coords.y >= area.y && coords.y <= area.y + area.height
    );

    if (clickedAreaIndex !== -1) {
      setSelectedArea(clickedAreaIndex);
      setIsDrawing(false);
    } else {
      // Start drawing new area
      setSelectedArea(null);
      setIsDrawing(true);
      setDrawStart(coords);
    }
  };

  const handleCanvasMouseMove = event => {
    if (!isDrawing || !drawStart || !backgroundImage) return;

    const coords = getCanvasCoordinates(event);
    const width = Math.abs(coords.x - drawStart.x);
    const height = Math.abs(coords.y - drawStart.y);
    const x = Math.min(coords.x, drawStart.x);
    const y = Math.min(coords.y, drawStart.y);

    // Update temporary area (we'll add this to designAreas on mouse up)
    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');

    // Redraw everything
    drawCanvas();

    // Draw temporary rectangle
    ctx.strokeStyle = '#10b981';
    ctx.lineWidth = 2;
    ctx.setLineDash([3, 3]);
    ctx.strokeRect(x * scale, y * scale, width * scale, height * scale);
    ctx.fillStyle = 'rgba(16, 185, 129, 0.1)';
    ctx.fillRect(x * scale, y * scale, width * scale, height * scale);
  };

  const handleCanvasMouseUp = event => {
    if (!isDrawing || !drawStart || !backgroundImage) return;

    const coords = getCanvasCoordinates(event);
    const width = Math.abs(coords.x - drawStart.x);
    const height = Math.abs(coords.y - drawStart.y);
    const x = Math.min(coords.x, drawStart.x);
    const y = Math.min(coords.y, drawStart.y);

    // Only create area if it has meaningful size
    if (width > 10 && height > 10) {
      const newArea = {
        x: Math.round(x),
        y: Math.round(y),
        width: Math.round(width),
        height: Math.round(height),
        rotation: 0,
        name: `Design Area ${designAreas.length + 1}`,
      };

      setDesignAreas([...designAreas, newArea]);
      setSelectedArea(designAreas.length);
    }

    setIsDrawing(false);
    setDrawStart(null);
  };

  const updateSelectedArea = (field, value) => {
    if (selectedArea === null) return;

    const updatedAreas = [...designAreas];
    updatedAreas[selectedArea] = {
      ...updatedAreas[selectedArea],
      [field]: field === 'name' ? value : parseFloat(value) || 0,
    };
    setDesignAreas(updatedAreas);
  };

  const deleteSelectedArea = () => {
    if (selectedArea === null) return;

    const updatedAreas = designAreas.filter((_, index) => index !== selectedArea);
    setDesignAreas(updatedAreas);
    setSelectedArea(null);
  };

  const generatePreview = async () => {
    if (!backgroundImage || designAreas.length === 0) {
      addNotification('Please add a background image and at least one design area', 'error');
      return;
    }

    try {
      setLoading(true);

      // Convert background image to base64 if it's not already
      let imageData = backgroundImage;
      if (backgroundImage.startsWith('data:')) {
        imageData = backgroundImage.split(',')[1];
      }

      const previewData = {
        template_id: 'preview', // Special ID for preview mode
        design_areas: designAreas,
        background_image_data: imageData,
        background_filename: backgroundFile?.name || 'background.png',
      };

      // For now, just show the current canvas as preview
      // In production, you'd call the backend preview endpoint
      const canvas = canvasRef.current;
      const previewDataUrl = canvas.toDataURL();
      setPreviewImage(previewDataUrl);
      setPreviewMode(true);

      addNotification('Preview generated successfully', 'success');
    } catch (error) {
      console.error('Error generating preview:', error);
      addNotification('Failed to generate preview', 'error');
    } finally {
      setLoading(false);
    }
  };

  const saveTemplate = async () => {
    if (!templateData.name.trim()) {
      addNotification('Please enter a template name', 'error');
      return;
    }

    if (!backgroundImage) {
      addNotification('Please upload a background image', 'error');
      return;
    }

    if (designAreas.length === 0) {
      addNotification('Please define at least one design area', 'error');
      return;
    }

    try {
      setLoading(true);

      // Convert background image to base64
      let imageData = backgroundImage;
      if (backgroundImage.startsWith('data:')) {
        imageData = backgroundImage.split(',')[1];
      }

      const templatePayload = {
        name: templateData.name,
        description: templateData.description,
        category: templateData.category,
        background_image_data: imageData,
        background_filename: backgroundFile?.name || 'background.png',
        design_areas: designAreas,
        metadata: {},
      };

      const response = await fetch('/api/templates/', {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(templatePayload),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save template');
      }

      const savedTemplate = await response.json();

      addNotification('Template saved successfully!', 'success');

      // Reset form
      setTemplateData({ name: '', description: '', category: '' });
      setBackgroundImage(null);
      setBackgroundFile(null);
      setDesignAreas([]);
      setSelectedArea(null);
    } catch (error) {
      console.error('Error saving template:', error);
      addNotification(`Failed to save template: ${error.message}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Template Editor</h1>
          <p className="text-gray-600">Create product templates with design areas</p>
        </div>
        <div className="flex space-x-3">
          <button
            onClick={generatePreview}
            disabled={!backgroundImage || designAreas.length === 0 || loading}
            className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <EyeIcon className="w-4 h-4 mr-2" />
            Preview
          </button>
          <button
            onClick={saveTemplate}
            disabled={!templateData.name || !backgroundImage || designAreas.length === 0 || loading}
            className="flex items-center px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" /> : <CheckIcon className="w-4 h-4 mr-2" />}
            Save Template
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left Panel - Template Info & Design Areas */}
        <div className="lg:col-span-1 space-y-6">
          {/* Template Information */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Template Information</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Template Name *</label>
                <input
                  type="text"
                  value={templateData.name}
                  onChange={e => setTemplateData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  placeholder="Enter template name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Description</label>
                <textarea
                  value={templateData.description}
                  onChange={e => setTemplateData(prev => ({ ...prev, description: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                  rows="3"
                  placeholder="Describe your template"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Category</label>
                <select
                  value={templateData.category}
                  onChange={e => setTemplateData(prev => ({ ...prev, category: e.target.value }))}
                  className="w-full border border-gray-300 rounded-md px-3 py-2"
                >
                  <option value="">Select category</option>
                  <option value="apparel">Apparel</option>
                  <option value="accessories">Accessories</option>
                  <option value="home">Home & Living</option>
                  <option value="stationery">Stationery</option>
                  <option value="other">Other</option>
                </select>
              </div>
            </div>
          </div>

          {/* Background Upload */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Background Image</h3>

            <div className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                onChange={handleBackgroundUpload}
                className="hidden"
              />

              <button
                onClick={() => fileInputRef.current?.click()}
                className="w-full flex flex-col items-center justify-center p-6 border-2 border-dashed border-gray-300 rounded-lg hover:border-sage-400 transition-colors"
              >
                <CloudArrowUpIcon className="w-8 h-8 text-gray-400 mb-2" />
                <span className="text-sm text-gray-600">
                  {backgroundFile ? backgroundFile.name : 'Click to upload background'}
                </span>
              </button>

              {backgroundImage && (
                <div className="text-center">
                  <img
                    src={backgroundImage}
                    alt="Background preview"
                    className="max-w-full h-20 object-contain mx-auto rounded border"
                  />
                  <p className="text-xs text-gray-500 mt-1">Background loaded</p>
                </div>
              )}
            </div>
          </div>

          {/* Design Areas List */}
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Design Areas</h3>
              <span className="text-sm text-gray-500">{designAreas.length} areas</span>
            </div>

            {designAreas.length === 0 ? (
              <div className="text-center py-4">
                <CursorArrowRippleIcon className="w-8 h-8 text-gray-400 mx-auto mb-2" />
                <p className="text-sm text-gray-500">Click and drag on the canvas to create design areas</p>
              </div>
            ) : (
              <div className="space-y-2">
                {designAreas.map((area, index) => (
                  <div
                    key={index}
                    className={`p-3 rounded border cursor-pointer transition-colors ${
                      selectedArea === index ? 'border-blue-500 bg-blue-50' : 'border-gray-200 hover:bg-gray-50'
                    }`}
                    onClick={() => setSelectedArea(index)}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-medium">{area.name}</span>
                      {selectedArea === index && (
                        <button
                          onClick={e => {
                            e.stopPropagation();
                            deleteSelectedArea();
                          }}
                          className="text-red-500 hover:text-red-700"
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      )}
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {Math.round(area.width)} × {Math.round(area.height)} px
                    </div>
                  </div>
                ))}
              </div>
            )}

            {/* Selected Area Editor */}
            {selectedArea !== null && (
              <div className="mt-4 pt-4 border-t border-gray-200">
                <h4 className="text-sm font-medium text-gray-900 mb-3">Edit Selected Area</h4>

                <div className="space-y-3">
                  <div>
                    <label className="block text-xs font-medium text-gray-700 mb-1">Name</label>
                    <input
                      type="text"
                      value={designAreas[selectedArea]?.name || ''}
                      onChange={e => updateSelectedArea('name', e.target.value)}
                      className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">X</label>
                      <input
                        type="number"
                        value={Math.round(designAreas[selectedArea]?.x || 0)}
                        onChange={e => updateSelectedArea('x', e.target.value)}
                        className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Y</label>
                      <input
                        type="number"
                        value={Math.round(designAreas[selectedArea]?.y || 0)}
                        onChange={e => updateSelectedArea('y', e.target.value)}
                        className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Width</label>
                      <input
                        type="number"
                        value={Math.round(designAreas[selectedArea]?.width || 0)}
                        onChange={e => updateSelectedArea('width', e.target.value)}
                        className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                    <div>
                      <label className="block text-xs font-medium text-gray-700 mb-1">Height</label>
                      <input
                        type="number"
                        value={Math.round(designAreas[selectedArea]?.height || 0)}
                        onChange={e => updateSelectedArea('height', e.target.value)}
                        className="w-full text-sm border border-gray-300 rounded px-2 py-1"
                      />
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Main Canvas Area */}
        <div className="lg:col-span-3">
          <div className="bg-white rounded-lg shadow-lg p-6">
            <div className="flex items-center justify-between mb-4">
              <h3 className="text-lg font-semibold text-gray-900">Design Canvas</h3>
              {backgroundImage && <div className="text-sm text-gray-600">Scale: {Math.round(scale * 100)}%</div>}
            </div>

            <div className="border border-gray-300 rounded-lg overflow-hidden bg-gray-50">
              {backgroundImage ? (
                <div className="relative">
                  <img ref={imageRef} src={backgroundImage} alt="Background" className="hidden" />
                  <canvas
                    ref={canvasRef}
                    onMouseDown={handleCanvasMouseDown}
                    onMouseMove={handleCanvasMouseMove}
                    onMouseUp={handleCanvasMouseUp}
                    className="cursor-crosshair bg-white"
                    style={{ maxWidth: '100%', height: 'auto' }}
                  />

                  <div className="absolute bottom-4 left-4 bg-black bg-opacity-75 text-white px-3 py-1 rounded text-sm">
                    Click and drag to create design areas
                  </div>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center h-96 text-gray-500">
                  <PhotoIcon className="w-16 h-16 mb-4" />
                  <p className="text-lg font-medium">Upload a background image to start</p>
                  <p className="text-sm">Click the upload button in the left panel</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Preview Modal */}
      {previewMode && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl max-h-full overflow-auto">
            <div className="flex items-center justify-between p-6 border-b">
              <h3 className="text-lg font-semibold">Template Preview</h3>
              <button onClick={() => setPreviewMode(false)} className="text-gray-400 hover:text-gray-600">
                <XMarkIcon className="w-6 h-6" />
              </button>
            </div>

            <div className="p-6">
              {previewImage && (
                <img src={previewImage} alt="Template preview" className="max-w-full h-auto mx-auto rounded border" />
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default TemplateEditor;
