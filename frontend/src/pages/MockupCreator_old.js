import React, { useState, useRef, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const MockupCreator = () => {
  const api = useApi();
  const [mockupImage, setMockupImage] = useState(null);
  const [points, setPoints] = useState([]);
  const [drawingMode, setDrawingMode] = useState('point'); // 'point' or 'rectangle'
  const [rectStart, setRectStart] = useState(null);
  const [masks, setMasks] = useState([]);
  const [currentMaskIndex, setCurrentMaskIndex] = useState(0);
  const [numMasks, setNumMasks] = useState(1);
  const [isDrawing, setIsDrawing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('');
  const [templates, setTemplates] = useState([]);
  const [loadingTemplates, setLoadingTemplates] = useState(true);
  const [message, setMessage] = useState('');
  const [existingMaskData, setExistingMaskData] = useState(null);
  const [loadingMaskData, setLoadingMaskData] = useState(false);
  const canvasRef = useRef(null);
  const [scaleFactor, setScaleFactor] = useState(1.0);
  const [startingName, setStartingName] = useState(100);
  const [storedMasks, setStoredMasks] = useState([]);
  const [storedImageSize, setStoredImageSize] = useState({ width: 0, height: 0 });
  const [showMockupModal, setShowMockupModal] = useState(false);
  const [baseMockups, setBaseMockups] = useState([]);
  const [loadingBaseMockups, setLoadingBaseMockups] = useState(false);
  const [mockupError, setMockupError] = useState('');

  // Load user templates on component mount
  useEffect(() => {
    loadUserTemplates();
  }, []);

  // Load existing mask data when template is selected
  useEffect(() => {
    if (selectedTemplate) {
      loadExistingMaskData(selectedTemplate);
    }
  }, [selectedTemplate]);

  const loadUserTemplates = async () => {
    try {
      setLoadingTemplates(true);
      const response = await api.get('/api/user-templates');
      setTemplates(response);

      // Set default template if available
      if (response.length > 0) {
        setSelectedTemplate(response[0].name);
      }
    } catch (error) {
      console.error('Error loading templates:', error);
      setMessage('Failed to load templates');
    } finally {
      setLoadingTemplates(false);
    }
  };

  const loadExistingMaskData = async templateName => {
    if (!templateName) {
      setExistingMaskData(null);
      return;
    }

    try {
      setLoadingMaskData(true);
      const response = await api.get(`/api/user-mask-data/${templateName}`);

      if (response.success) {
        setExistingMaskData(response);
        setMessage(`Found existing mask data for ${templateName}: ${response.masks_count} masks`);
      } else {
        setExistingMaskData(null);
        setMessage(`No existing mask data found for ${templateName}`);
      }
    } catch (error) {
      console.error('Error loading mask data:', error);
      setExistingMaskData(null);
      setMessage('Failed to load existing mask data');
    } finally {
      setLoadingMaskData(false);
    }
  };

  const openMockupModal = async () => {
    setShowMockupModal(true);
    setMockupError('');
    setLoadingBaseMockups(true);
    try {
      if (selectedTemplate) {
        const response = await api.get(`/api/base-mockups/${selectedTemplate}`);
        setBaseMockups(response.images || []);
      } else {
        setBaseMockups([]);
      }
    } catch (e) {
      setBaseMockups([]);
      setMockupError('Failed to load base mockups');
    } finally {
      setLoadingBaseMockups(false);
    }
  };

  const handleSelectBaseMockup = async url => {
    try {
      const img = new window.Image();
      img.crossOrigin = 'anonymous';
      img.onload = () => {
        setMockupImage(img);
        setShowMockupModal(false);
        setMockupError('');
        // Calculate scale factor for display
        const maxSize = 1200;
        const scale = Math.min(maxSize / img.width, maxSize / img.height);
        setScaleFactor(scale);
      };
      img.onerror = () => setMockupError('Failed to load image');
      img.src = url;
    } catch (e) {
      setMockupError('Failed to load image');
    }
  };

  const handleUploadMockup = event => {
    const file = event.target.files[0];
    if (!file) return;
    const img = new window.Image();
    const reader = new FileReader();
    reader.onload = e => {
      img.onload = () => {
        if (img.width > 2048 || img.height > 2048) {
          setMockupError('Image must be 2048x2048 pixels or smaller');
          return;
        }
        setMockupImage(img);
        setShowMockupModal(false);
        setMockupError('');
        // Calculate scale factor for display
        const maxSize = 1200;
        const scale = Math.min(maxSize / img.width, maxSize / img.height);
        setScaleFactor(scale);
      };
      img.onerror = () => setMockupError('Failed to load image');
      img.src = e.target.result;
    };
    reader.readAsDataURL(file);
  };

  const getCanvasContext = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    return { canvas, ctx };
  };

  const drawImage = () => {
    const context = getCanvasContext();
    if (!context || !context.canvas || !context.ctx || !mockupImage) return;
    const { canvas, ctx } = context;

    // Set canvas size
    const displayWidth = mockupImage.width * scaleFactor;
    const displayHeight = mockupImage.height * scaleFactor;
    canvas.width = displayWidth;
    canvas.height = displayHeight;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw mockup image
    ctx.drawImage(mockupImage, 0, 0, displayWidth, displayHeight);

    // Draw existing masks
    masks.forEach((mask, index) => {
      if (index < currentMaskIndex) {
        drawMask(mask.points, index === currentMaskIndex - 1 ? '#00ff00' : '#ffff00');
      }
    });

    // Draw current points
    drawPoints();
  };

  const drawPoints = () => {
    const context = getCanvasContext();
    if (!context || !context.ctx) return;
    const { ctx } = context;

    // Draw points
    points.forEach((point, index) => {
      ctx.beginPath();
      ctx.arc(point.x, point.y, 5, 0, 2 * Math.PI);
      ctx.fillStyle = '#00ff00';
      ctx.fill();
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 2;
      ctx.stroke();

      // Add point numbers
      ctx.fillStyle = '#ffffff';
      ctx.font = '16px Arial';
      ctx.fillText(index + 1, point.x + 8, point.y - 8);
    });

    // Draw lines between points
    if (points.length > 1) {
      ctx.beginPath();
      ctx.moveTo(points[0].x, points[0].y);
      for (let i = 1; i < points.length; i++) {
        ctx.lineTo(points[i].x, points[i].y);
      }
      ctx.strokeStyle = '#00ffff';
      ctx.lineWidth = 2;
      ctx.stroke();
    }

    // Draw rectangle preview
    if (drawingMode === 'rectangle' && rectStart) {
      // Note: We can't get mouse position here without the event
      // The rectangle preview will be updated on mouse move
    }
  };

  const drawMask = (maskPoints, color) => {
    const context = getCanvasContext();
    if (!context || !context.ctx || !maskPoints.length) return;
    const { ctx } = context;

    ctx.beginPath();
    ctx.moveTo(maskPoints[0].x, maskPoints[0].y);
    for (let i = 1; i < maskPoints.length; i++) {
      ctx.lineTo(maskPoints[i].x, maskPoints[i].y);
    }
    ctx.closePath();
    ctx.strokeStyle = color;
    ctx.lineWidth = 3;
    ctx.stroke();
    ctx.fillStyle = color + '40';
    ctx.fill();
  };

  const getMousePos = event => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height),
    };
  };

  const handleCanvasClick = event => {
    if (!mockupImage) return;

    const mousePos = getMousePos(event);
    if (!mousePos) return;

    if (drawingMode === 'point') {
      setPoints([...points, mousePos]);
    } else if (drawingMode === 'rectangle') {
      if (!rectStart) {
        setRectStart(mousePos);
      } else {
        // Create rectangle points
        const rectPoints = [rectStart, { x: mousePos.x, y: rectStart.y }, mousePos, { x: rectStart.x, y: mousePos.y }];
        setPoints(rectPoints);
        setRectStart(null);
      }
    }
  };

  const handleCanvasMouseMove = event => {
    if (drawingMode === 'rectangle' && rectStart) {
      const mousePos = getMousePos(event);
      if (mousePos) {
        // Redraw with rectangle preview
        drawImage();
        const { ctx } = getCanvasContext();
        if (ctx) {
          ctx.strokeStyle = '#00ffff';
          ctx.lineWidth = 2;
          ctx.setLineDash([5, 5]);
          ctx.strokeRect(rectStart.x, rectStart.y, mousePos.x - rectStart.x, mousePos.y - rectStart.y);
          ctx.setLineDash([]);
        }
      }
    }
  };

  const createMask = () => {
    if (points.length < 3) {
      setMessage('Need at least 3 points to create a mask');
      return;
    }

    // Scale points back to original image size
    const scaledPoints = points.map(point => ({
      x: point.x / scaleFactor,
      y: point.y / scaleFactor,
    }));

    console.log('DEBUG: Scaled points:', scaledPoints);
    const newMask = {
      points: scaledPoints,
      displayPoints: [...points],
    };
    console.log('DEBUG: masks:', [...masks, newMask]);

    setMasks([...masks, newMask]);
    setPoints([]);
    setRectStart(null);
    setCurrentMaskIndex(currentMaskIndex + 1);

    if (currentMaskIndex + 1 >= numMasks) {
      // All masks created
      saveMasks([...masks, newMask]);
    }
  };

  const resetCurrentMask = () => {
    setPoints([]);
    setRectStart(null);
    setMessage('');
  };

  const saveMasks = async masks_data => {
    if (!selectedTemplate) {
      setMessage('Please select a template first');
      return;
    }

    if (existingMaskData) {
      setMessage('Please clear existing mask data first or select a different template');
      return;
    }

    try {
      setIsSaving(true);
      setMessage('');
      const maskPoints = masks_data.map(mask => mask.points);
      const imageWidth = mockupImage ? mockupImage.width : 1000;
      const imageHeight = mockupImage ? mockupImage.height : 1000;
      const dataToSend = {
        masks: maskPoints,
        points: maskPoints, // for compatibility
        starting_name: startingName,
        imageType: selectedTemplate,
        imageWidth,
        imageHeight,
      };
      console.log('DEBUG: Data being sent to API:', dataToSend);
      await api.post('/api/masks', dataToSend);

      setMessage('Masks saved successfully!');
      setMasks([]);
      setCurrentMaskIndex(0);
      setPoints([]);
      loadExistingMaskData(selectedTemplate);
      // Fetch and display stored masks
      fetchStoredMasks(selectedTemplate);
    } catch (error) {
      console.error('Error saving masks:', error);
      setMessage('Error saving masks: ' + (error.message || 'Unknown error'));
    } finally {
      setIsSaving(false);
    }
  };

  const fetchStoredMasks = async templateName => {
    try {
      const response = await api.get(`/api/user-mask-data/${templateName}`);
      if (response.success && response.masks && response.inspection) {
        // Use the inspection data to get the mask arrays and image size
        const maskAnalysis = response.inspection.mask_analysis || [];
        setStoredMasks(maskAnalysis.map(m => m.mask_array).filter(Boolean));
        setStoredImageSize({
          width: response.inspection.image_width || 1000,
          height: response.inspection.image_height || 1000,
        });
      } else {
        setStoredMasks([]);
        setStoredImageSize({ width: 0, height: 0 });
      }
    } catch (error) {
      setStoredMasks([]);
      setStoredImageSize({ width: 0, height: 0 });
    }
  };

  const setMode = mode => {
    setDrawingMode(mode);
    setPoints([]);
    setRectStart(null);
    setMessage('');
  };

  const resetAll = () => {
    setMasks([]);
    setCurrentMaskIndex(0);
    setPoints([]);
    setRectStart(null);
    setMessage('');
  };

  useEffect(() => {
    drawImage();
  }, [mockupImage, points, masks, currentMaskIndex, rectStart]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 py-4 sm:py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center text-white mb-6 sm:mb-8">
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2 sm:mb-4">Mockup Creator</h1>
          <p className="text-sm sm:text-base lg:text-xl opacity-90 px-4">
            Create masks for mockup images by drawing polygons or rectangles
          </p>
        </div>

        {/* Message Display */}
        {message && (
          <div
            className={`card p-4 mb-6 ${
              message.includes('successfully')
                ? 'bg-green-100 text-green-700 border border-green-300'
                : 'bg-red-100 text-red-700 border border-red-300'
            }`}
          >
            {message}
          </div>
        )}

        {/* Controls */}
        <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 sm:gap-6">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Select or Upload Mockup Image:</label>
              <button
                type="button"
                onClick={openMockupModal}
                className="input-field bg-blue-500 text-white hover:bg-blue-600 transition-colors"
              >
                Choose Mockup Image
              </button>
              {mockupImage && (
                <div className="mt-2 text-xs text-gray-600">Current image: {mockupImage.src.slice(0, 40)}...</div>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="template-select" className="block text-sm font-medium text-gray-700">
                Select Template:
              </label>
              {loadingTemplates ? (
                <div className="input-field bg-gray-100 text-gray-500">Loading templates...</div>
              ) : (
                <select
                  id="template-select"
                  value={selectedTemplate}
                  onChange={e => {
                    setSelectedTemplate(e.target.value);
                    loadExistingMaskData(e.target.value);
                  }}
                  className="input-field"
                >
                  <option value="">Select a template</option>
                  {templates.map(template => (
                    <option key={template.id} value={template.name}>
                      {template.template_title || template.name}
                    </option>
                  ))}
                </select>
              )}
            </div>

            <div className="space-y-2">
              <label htmlFor="num-masks" className="block text-sm font-medium text-gray-700">
                Number of Masks:
              </label>
              <select
                id="num-masks"
                value={numMasks}
                onChange={e => setNumMasks(parseInt(e.target.value))}
                className="input-field"
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Drawing Mode:</label>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <button
                  className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                    drawingMode === 'point' ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  onClick={() => setMode('point')}
                >
                  Point Mode
                </button>
                <button
                  className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                    drawingMode === 'rectangle'
                      ? 'bg-blue-500 text-white'
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  onClick={() => setMode('rectangle')}
                >
                  Rectangle Mode
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Actions:</label>
              <div className="flex flex-col sm:flex-row space-y-2 sm:space-y-0 sm:space-x-2">
                <button
                  onClick={createMask}
                  disabled={points.length < 3 || isSaving}
                  className={`px-3 py-2 rounded-lg font-medium transition-colors text-sm ${
                    points.length < 3 || isSaving
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-green-500 text-white hover:bg-green-600'
                  }`}
                >
                  {isSaving ? 'Saving...' : `Create Mask (${currentMaskIndex + 1}/${numMasks})`}
                </button>
                <button
                  onClick={resetCurrentMask}
                  disabled={isSaving}
                  className="px-3 py-2 bg-gray-500 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors disabled:opacity-50 text-sm"
                >
                  Reset Current
                </button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Reset All:</label>
              <button
                onClick={resetAll}
                disabled={isSaving}
                className="px-4 py-2 bg-red-500 text-white rounded-lg font-medium hover:bg-red-600 transition-colors disabled:opacity-50"
              >
                Reset All
              </button>
            </div>

            <div className="space-y-2">
              <label htmlFor="starting-name" className="block text-sm font-medium text-gray-700">
                Starting Name:
              </label>
              <input
                id="starting-name"
                type="number"
                min={1}
                value={startingName}
                onChange={e => setStartingName(Number(e.target.value))}
                className="input-field"
              />
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
          {mockupImage ? (
            <div className="flex justify-center overflow-x-auto">
              <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                className="border-2 border-gray-300 cursor-crosshair rounded-lg max-w-full"
              />
            </div>
          ) : (
            <div className="text-center py-8 sm:py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-8 w-8 sm:h-12 sm:w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <p className="text-gray-600 text-sm sm:text-base">Please upload a mockup image to start creating masks</p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Instructions:</h3>
          <ul className="space-y-2 text-gray-600 text-sm sm:text-base">
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>
                <strong>Select Template:</strong> Choose the template that will use these masks
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>
                <strong>Point Mode:</strong> Click to add points, then click "Create Mask" to close the shape
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>
                <strong>Rectangle Mode:</strong> Click and drag to create a rectangle
              </span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>You need at least 3 points to create a mask</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>Use "Reset Current" to start over with the current mask</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span>Masks will be automatically saved to the database when all are created</span>
            </li>
          </ul>
        </div>

        {/* Existing Mask Data */}
        {existingMaskData && (
          <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Existing Mask Data:</h3>
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-2 space-y-1 sm:space-y-0">
                <span className="text-sm font-medium text-blue-800">
                  Template: <strong>{existingMaskData.template_name}</strong>
                </span>
                <span className="text-sm text-blue-600">
                  {existingMaskData.masks_count} masks, {existingMaskData.points_count} point sets
                </span>
              </div>
              <p className="text-sm text-blue-700">Starting ID: {existingMaskData.starting_name}</p>
              <div className="mt-3">
                <button
                  onClick={() => {
                    setExistingMaskData(null);
                    setMessage('Existing mask data cleared. You can create new masks.');
                  }}
                  className="px-3 py-1 bg-blue-500 text-white text-sm rounded hover:bg-blue-600 transition-colors"
                >
                  Clear & Create New
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Mask Summary */}
        {masks.length > 0 && (
          <div className="card p-4 sm:p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Created Masks:</h3>
            <ul className="space-y-2">
              {masks.map((mask, index) => (
                <li key={index} className="flex items-center text-gray-600 text-sm sm:text-base">
                  <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    {index + 1}
                  </span>
                  Mask {index + 1}: {mask.points.length} points
                </li>
              ))}
            </ul>
            {selectedTemplate && (
              <p className="text-sm text-gray-500 mt-2">
                Template: <strong>{selectedTemplate}</strong>
              </p>
            )}
          </div>
        )}

        {/* Mask Visualizations */}
        {storedMasks.length > 0 && (
          <div className="card p-4 sm:p-6 mb-6 sm:mb-8">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Stored Mask Visualizations:</h3>
            <div className="flex flex-wrap gap-4">
              {storedMasks.map((maskArray, idx) => (
                <canvas
                  key={idx}
                  width={storedImageSize.width}
                  height={storedImageSize.height}
                  ref={el => {
                    if (el && maskArray) {
                      const ctx = el.getContext('2d');
                      const imgData = ctx.createImageData(storedImageSize.width, storedImageSize.height);
                      for (let y = 0; y < storedImageSize.height; y++) {
                        for (let x = 0; x < storedImageSize.width; x++) {
                          const i = y * storedImageSize.width + x;
                          const val = maskArray[y] && maskArray[y][x] ? maskArray[y][x] : 0;
                          imgData.data[i * 4 + 0] = val; // R
                          imgData.data[i * 4 + 1] = val; // G
                          imgData.data[i * 4 + 2] = val; // B
                          imgData.data[i * 4 + 3] = 255; // A
                        }
                      }
                      ctx.putImageData(imgData, 0, 0);
                    }
                  }}
                  style={{ border: '1px solid #ccc', background: '#fff', maxWidth: 200, maxHeight: 200 }}
                />
              ))}
            </div>
          </div>
        )}

        {/* Mockup Selection Modal */}
        {showMockupModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-40">
            <div className="bg-white rounded-lg shadow-lg p-6 max-w-lg w-full relative">
              <button
                className="absolute top-2 right-2 text-gray-500 hover:text-gray-700"
                onClick={() => setShowMockupModal(false)}
              >
                &times;
              </button>
              <h2 className="text-lg font-semibold mb-4">Select a Base Mockup or Upload</h2>
              {mockupError && <div className="mb-2 text-red-600">{mockupError}</div>}
              <div className="mb-4">
                <label className="block text-sm font-medium mb-1">Upload Custom Image (max 2048x2048):</label>
                <input type="file" accept="image/*" onChange={handleUploadMockup} className="input-field" />
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Or select a base mockup:</label>
                {loadingBaseMockups ? (
                  <div>Loading...</div>
                ) : (
                  <div className="flex flex-wrap gap-3 max-h-64 overflow-y-auto">
                    {baseMockups.length === 0 && <div className="text-gray-500">No base mockups found.</div>}
                    {baseMockups.map(img => (
                      <div
                        key={img.filename}
                        className="cursor-pointer border rounded hover:shadow-lg"
                        onClick={() => handleSelectBaseMockup(img.url)}
                        style={{ width: 100, height: 100, overflow: 'hidden' }}
                      >
                        <img
                          src={img.url}
                          alt={img.filename}
                          style={{ width: '100%', height: '100%', objectFit: 'cover' }}
                        />
                        <div className="text-xs text-center truncate">{img.filename}</div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default MockupCreator;
