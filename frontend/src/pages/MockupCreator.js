import React, { useState, useEffect, useRef } from 'react';
import { useApi } from '../hooks/useApi';
import { useSubscription } from '../hooks/useSubscription';
import { FeatureGate, UsageIndicator } from '../components/subscription';
import ViewMockupModal from '../components/ViewMockupModal';
import EditMockupModal from '../components/EditMockupModal';
import DeleteMockupModal from '../components/DeleteMockupModal';

const MockupCreator = () => {
  const api = useApi();
  const canvasRef = useRef(null);
  const { canCreateMockups, trackMockupCreation, remainingMockups, isFreeTier, FEATURES } = useSubscription();

  // Workflow state
  const [currentStep, setCurrentStep] = useState(1); // 1: Template, 2: Images, 3: Masks, 4: Final
  const [showModal, setShowModal] = useState(false);

  // Step 1: Template Selection
  const [templates, setTemplates] = useState([]);
  const [selectedTemplate, setSelectedTemplate] = useState(null);

  // Step 2: Image Selection
  const [selectedImages, setSelectedImages] = useState([]);
  const [imageFiles, setImageFiles] = useState([]);

  const [watermarkFile, setWatermarkFile] = useState(null);
  const [imageWatermarkFile, setImageWatermarkFile] = useState([]);

  // Step 3: Mask Creation
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [currentMaskIndex, setCurrentMaskIndex] = useState(0);
  const [masksPerImage, setMasksPerImage] = useState({}); // {imageIndex: numMasks}
  const [allMasks, setAllMasks] = useState({}); // {imageIndex: {maskIndex: {points, isPolygon, isCropped, alignment}}}

  // Canvas state
  const [points, setPoints] = useState([]);
  const [rectStart, setRectStart] = useState(null);
  const [drawingMode, setDrawingMode] = useState('point');
  const [isCropped, setIsCropped] = useState(false);
  const [alignment, setAlignment] = useState('center');
  const [currentImage, setCurrentImage] = useState(null);
  const [imageSize, setImageSize] = useState({ width: 0, height: 0 });
  const [scaleFactor, setScaleFactor] = useState(1.0);

  // Step 4: Final Details
  const [mockupName, setMockupName] = useState('');
  const [startingNumber, setStartingNumber] = useState(100);

  // UI state
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  // Existing mockups
  const [existingMockups, setExistingMockups] = useState([]);
  const [loadingMockups, setLoadingMockups] = useState(true);

  // Modal states
  const [viewModalOpen, setViewModalOpen] = useState(false);
  const [editModalOpen, setEditModalOpen] = useState(false);
  const [deleteModalOpen, setDeleteModalOpen] = useState(false);
  const [selectedMockup, setSelectedMockup] = useState(null);

  useEffect(() => {
    loadTemplates();
    loadExistingMockups();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const setMode = mode => {
    setDrawingMode(mode);
    setPoints([]);
    setRectStart(null);
    setMessage('');
  };

  const loadTemplates = async () => {
    try {
      const response = await api.get('/settings/product-template');
      setTemplates(response);
    } catch (error) {
      console.error('Error loading templates:', error);
      setMessage('Failed to load templates');
    }
  };

  const loadExistingMockups = async () => {
    try {
      setLoadingMockups(true);
      const response = await api.get('/mockups/');
      setExistingMockups(response.mockups || []);
    } catch (error) {
      console.error('Error loading mockups:', error);
      setMessage('Failed to load existing mockups');
    } finally {
      setLoadingMockups(false);
    }
  };

  // Modal handlers
  const handleViewMockup = mockup => {
    setSelectedMockup(mockup);
    setViewModalOpen(true);
  };

  const handleEditMockup = mockup => {
    setSelectedMockup(mockup);
    setEditModalOpen(true);
  };

  const handleDeleteMockup = mockup => {
    setSelectedMockup(mockup);
    setDeleteModalOpen(true);
  };

  const handleModalClose = () => {
    setViewModalOpen(false);
    setEditModalOpen(false);
    setDeleteModalOpen(false);
    setSelectedMockup(null);
  };

  const handleMockupUpdate = () => {
    loadExistingMockups();
  };

  const handleMockupDelete = () => {
    loadExistingMockups();
  };

  const handleImageUpload = event => {
    const files = Array.from(event.target.files);
    setImageFiles(files);
    setSelectedImages(files.map(file => URL.createObjectURL(file)));
  };

  const handleImageWatermarkUpload = event => {
    const file = event.target.files[0];
    const files = Array(file);
    setWatermarkFile(file || null);
    setImageWatermarkFile(files.map(f => URL.createObjectURL(f)));
    console.log('Watermark file set:', file);
  };

  // Replace drawImage and drawPoints with the more advanced logic from MockupCreator.js
  const getCanvasContext = () => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    return { canvas, ctx };
  };

  const drawImage = () => {
    const context = getCanvasContext();
    if (!context || !context.canvas || !context.ctx || !currentImage) return;
    const { canvas, ctx } = context;

    const img = new window.Image();
    img.onload = () => {
      // Set canvas size
      let displayWidth = img.width;
      let displayHeight = img.height;
      // Calculate scale factor for display (max 900x700)
      const maxWidth = 900;
      const maxHeight = 700;
      const scale = Math.min(maxWidth / img.width, maxHeight / img.height, 1);
      displayWidth = img.width * scale;
      displayHeight = img.height * scale;
      setScaleFactor(scale);
      canvas.width = displayWidth;
      canvas.height = displayHeight;
      setImageSize({ width: displayWidth, height: displayHeight });
      // Clear canvas
      ctx.clearRect(0, 0, canvas.width, canvas.height);
      // Draw image
      ctx.drawImage(img, 0, 0, displayWidth, displayHeight);
      // Draw current points and overlays
      drawPoints();
    };
    img.src = currentImage;
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
      // Draw preview rectangle
      ctx.strokeStyle = '#00ffff';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(rectStart.x, rectStart.y, points[0]?.x - rectStart.x, points[0]?.y - rectStart.y);
      ctx.setLineDash([]);
    }
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
    if (!currentImage) return;
    const mousePos = getMousePos(event);
    if (!mousePos) return;
    console.log(rectStart);
    if (drawingMode === 'point') {
      setPoints([...points, mousePos]);
    } else if (drawingMode === 'rectangle') {
      if (!rectStart) {
        setRectStart(mousePos);
        setPoints([mousePos]);
      } else {
        console.log(mousePos);
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
        // Update rectangle preview
        setPoints([mousePos]);
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

    const scaledPoints = points.map(point => ({
      x: point.x / scaleFactor,
      y: point.y / scaleFactor,
    }));

    const maskData = {
      points: scaledPoints,
      displayPoints: [...points],
      isCropped: isCropped,
      alignment: alignment,
    };

    setAllMasks(prev => ({
      ...prev,
      [currentImageIndex]: {
        ...prev[currentImageIndex],
        [currentMaskIndex]: maskData,
      },
    }));

    // Move to next mask or next image
    const currentImageMasks = masksPerImage[currentImageIndex] || 1;
    if (currentMaskIndex < currentImageMasks - 1) {
      setCurrentMaskIndex(prev => prev + 1);
      setPoints([]);
      setRectStart(null);
    } else {
      // Move to next image
      if (currentImageIndex < selectedImages.length - 1) {
        setCurrentImageIndex(prev => prev + 1);
        setCurrentMaskIndex(0);
        setPoints([]);
        setRectStart(null);
      } else {
        // All done, move to final step
        setCurrentStep(5);
      }
    }
  };

  const resetCurrentMask = () => {
    setPoints([]);
    setRectStart(null);
  };

  const goToNextStep = () => {
    if (currentStep === 1 && !selectedTemplate) {
      setMessage('Please select a template');
      return;
    }
    if (currentStep === 2 && selectedImages.length === 0) {
      setMessage('Please select at least one image');
      return;
    }

    if (currentStep === 3 && imageWatermarkFile.length === 0) {
      setMessage('Please select at least one image');
      return;
    }

    setCurrentStep(prev => prev + 1);
    setMessage('');
  };

  const goToPreviousStep = () => {
    setCurrentStep(prev => prev - 1);
    setMessage('');
  };

  const startWorkflow = () => {
    setShowModal(true);
    setCurrentStep(1);
    setSelectedTemplate(null);
    setSelectedImages([]);
    setImageFiles([]);
    setWatermarkFile(null);
    setImageWatermarkFile([]);
    setCurrentImageIndex(0);
    setCurrentMaskIndex(0);
    setMasksPerImage({});
    setAllMasks({});
    setMockupName('');
    setStartingNumber(100);
    setMessage('');
  };

  const createMockup = async () => {
    if (!mockupName.trim()) {
      setMessage('Please enter a mockup name');
      return;
    }

    // Check if user can create mockups
    if (!canCreateMockups) {
      setMessage(
        `You've reached your monthly mockup limit. ${isFreeTier ? 'Upgrade to Pro for unlimited mockups!' : 'Please check your subscription status.'}`
      );
      return;
    }

    setLoading(true);
    try {
      // Create mockup group
      const mockupGroup = await api.post('/mockups/group', {
        name: mockupName,
        product_template_id: selectedTemplate.id,
        starting_name: startingNumber,
      });

      // Upload all images at once
      const formData = new FormData();
      imageFiles.forEach(file => {
        formData.append('files', file);
      });
      formData.append('mockup_id', mockupGroup.id);
      formData.append('watermark_file', watermarkFile);

      const uploadResponse = await api.postFormData('/mockups/upload', formData);
      const uploadedImages = uploadResponse.uploaded_images || uploadResponse;

      // Create mask data for each image
      // Ensure we have the same number of uploaded images as selected images
      if (uploadedImages.length !== selectedImages.length) {
        console.error('Mismatch between uploaded images and selected images count');
        setMessage('Error: Uploaded images count does not match selected images');
        return;
      }

      for (let imageIndex = 0; imageIndex < selectedImages.length; imageIndex++) {
        const imageMasks = allMasks[imageIndex] || {};
        const uploadedImage = uploadedImages[imageIndex];

        if (!uploadedImage) {
          console.error(`No uploaded image found for image index ${imageIndex}`);
          continue;
        }

        // Get all masks for this image
        const maskKeys = Object.keys(imageMasks);
        if (maskKeys.length > 0) {
          // Prepare all masks for this image with individual properties
          const allMasksForImage = [];
          const allPointsForImage = [];
          const allIsCroppedForImage = [];
          const allAlignmentsForImage = [];

          maskKeys.forEach(maskIndex => {
            const maskData = imageMasks[maskIndex];
            if (maskData && maskData.points) {
              // Convert points from {x, y} objects to [x, y] arrays
              const convertedPoints = maskData.points.map(point => [point.x, point.y]);
              allMasksForImage.push(convertedPoints);
              allPointsForImage.push(convertedPoints);
              allIsCroppedForImage.push(maskData.isCropped || false);
              allAlignmentsForImage.push(maskData.alignment || 'center');
            }
          });

          // Use the first mask's properties for backward compatibility
          const firstMask = imageMasks[Object.keys(imageMasks)[0]];

          console.log('Sending mask data for image', imageIndex, 'with image ID', uploadedImage.id, ':', {
            masks: allMasksForImage,
            points: allPointsForImage,
            is_cropped: firstMask?.isCropped || false,
            alignment: firstMask?.alignment || 'center',
            is_cropped_list: allIsCroppedForImage,
            alignment_list: allAlignmentsForImage,
          });

          // Create mask data using the actual image ID with individual mask properties
          await api.post(`/mockups/images/${uploadedImage.id}/mask-data`, {
            mockup_image_id: uploadedImage.id,
            masks: allMasksForImage,
            points: allPointsForImage,
            is_cropped: firstMask?.isCropped || false, // Keep for backward compatibility
            alignment: firstMask?.alignment || 'center', // Keep for backward compatibility
            is_cropped_list: allIsCroppedForImage, // Individual mask properties
            alignment_list: allAlignmentsForImage, // Individual mask properties
          });
        } else {
          console.warn(`No mask data found for image index ${imageIndex}`);
        }
      }

      setMessage('Mockup created successfully!');
      trackMockupCreation(); // Track usage for subscription limits
      setShowModal(false);
      loadExistingMockups(); // Refresh the mockups list
    } catch (error) {
      console.error('Error creating mockup:', error);
      setMessage('Failed to create mockup');
    } finally {
      setLoading(false);
    }
  };

  // Update current image when image index changes
  useEffect(() => {
    if (selectedImages.length > 0 && currentImageIndex < selectedImages.length) {
      setCurrentImage(selectedImages[currentImageIndex]);
    }
  }, [currentImageIndex, selectedImages]);

  // Redraw canvas when image changes
  useEffect(() => {
    drawImage();
  }, [currentImage]); // eslint-disable-line react-hooks/exhaustive-deps

  // Redraw points when they change
  useEffect(() => {
    drawPoints();
  }, [points]); // eslint-disable-line react-hooks/exhaustive-deps

  const renderStep1 = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">Step 1: Select Template</h3>
      <p className="text-gray-600">Choose the template that will be associated with your mockups.</p>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {templates.map(template => (
          <div
            key={template.id}
            onClick={() => setSelectedTemplate(template)}
            className={`p-4 border-2 rounded-lg cursor-pointer transition-all ${
              selectedTemplate?.id === template.id
                ? 'border-blue-500 bg-blue-50'
                : 'border-gray-200 hover:border-gray-300'
            }`}
          >
            <h4 className="font-semibold text-gray-900">{template.name}</h4>
            {template.template_title && <p className="text-sm text-gray-600">{template.template_title}</p>}
            <div className="text-xs text-gray-500 mt-2">
              <div>Price: ${template.price || 0}</div>
              <div>Type: {template.type || 'N/A'}</div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );

  const renderStep2 = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">Step 2: Select Images</h3>
      <p className="text-gray-600">Choose one or more images to create mockups from.</p>

      <div className="space-y-4">
        <input
          type="file"
          multiple
          accept="image/*"
          onChange={handleImageUpload}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        {selectedImages.length > 0 && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {selectedImages.map((url, index) => (
              <div key={index} className="relative">
                <img
                  src={url}
                  alt={`Design ${index + 1}`}
                  className="w-full h-32 object-cover rounded-lg border-2 border-gray-200"
                />
                <div className="absolute top-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">
                  {index + 1}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );

  const renderStep2_5 = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">Step 2.5: Select Watermark Image</h3>
      <p className="text-gray-600">Choose one image to create mockups from.</p>

      <div className="space-y-4">
        <input
          type="file"
          accept="image/*"
          onChange={handleImageWatermarkUpload}
          className="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100"
        />

        {watermarkFile !== null && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            <div key={1} className="relative">
              <img
                src={watermarkFile.url}
                alt={`Watermark`}
                className="w-full h-32 object-cover rounded-lg border-2 border-gray-200"
              />
              <div className="absolute top-2 right-2 bg-blue-500 text-white text-xs px-2 py-1 rounded">{1}</div>
            </div>
          </div>
        )}
      </div>
    </div>
  );

  const renderStep3 = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">Step 3: Create Masks</h3>
      <p className="text-gray-600">
        Creating masks for image {currentImageIndex + 1} of {selectedImages.length}
      </p>

      {/* Image Progress */}
      <div className="flex items-center space-x-4">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-500 h-2 rounded-full transition-all"
            style={{ width: `${((currentImageIndex + 1) / selectedImages.length) * 100}%` }}
          />
        </div>
        <span className="text-sm text-gray-600">
          {currentImageIndex + 1} / {selectedImages.length}
        </span>
      </div>

      {/* Current Image */}
      <div className="flex justify-center">
        <img
          src={selectedImages[currentImageIndex]}
          alt={`Design ${currentImageIndex + 1}`}
          className="max-h-64 object-contain rounded-lg border-2 border-gray-200"
        />
      </div>

      {/* Mask Configuration */}
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Number of masks for this image:</label>
          <input
            type="number"
            min="1"
            max="10"
            value={masksPerImage[currentImageIndex] || 1}
            onChange={e =>
              setMasksPerImage(prev => ({
                ...prev,
                [currentImageIndex]: parseInt(e.target.value) || 1,
              }))
            }
            className="w-20 px-3 py-2 border border-gray-300 rounded-lg"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Mask {currentMaskIndex + 1} of {masksPerImage[currentImageIndex] || 1}
          </label>

          {/* Mode Selection */}
          <div className="flex space-x-4 mb-4">
            <label className="flex items-center">
              <input
                type="radio"
                checked={drawingMode === 'point'}
                onChange={() => setMode('point')}
                className="mr-2"
              />
              <span className="text-sm">Point Mode</span>
            </label>
            <label className="flex items-center">
              <input
                type="radio"
                checked={drawingMode === 'rectangle'}
                onChange={() => setMode('rectangle')}
                className="mr-2"
              />
              <span className="text-sm">Rectangle Mode</span>
            </label>
            <label className="flex items-center">
              <input type="checkbox" checked={isCropped} onChange={() => setIsCropped(!isCropped)} className="mr-2" />
              <span className="text-sm">Crop Image</span>
            </label>
            <label className="flex items-center">
              <select
                value={alignment || 'center'}
                onChange={e => setAlignment(e.target.value)}
                className="mr-2 px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value="left">Left</option>
                <option value="center">Center</option>
                <option value="right">Right</option>
              </select>
              <span className="text-sm">Select Alignment</span>
            </label>
          </div>

          {/* Canvas */}
          <div className="border-2 border-gray-300 rounded-lg overflow-hidden bg-gray-50">
            <canvas
              ref={canvasRef}
              onClick={handleCanvasClick}
              onMouseMove={handleCanvasMouseMove}
              className="cursor-crosshair block mx-auto"
              style={{
                maxWidth: '900px',
                maxHeight: '700px',
                width: imageSize.width ? Math.min(imageSize.width, 900) : 900,
                height: imageSize.height ? Math.min(imageSize.height, 700) : 700,
                display: 'block',
              }}
            />
          </div>

          {/* Instructions */}
          <div className="mt-4 text-sm text-gray-600">
            {drawingMode === 'points' ? (
              <p>Click to add points. You need at least 3 points to create a mask.</p>
            ) : (
              <p>Click and drag to create a rectangle mask.</p>
            )}
            <p className="mt-2 text-xs text-gray-500">
              Canvas size: {imageSize.width} x {imageSize.height} | Points: {points.length}
            </p>
          </div>

          {/* Actions */}
          <div className="flex space-x-4 mt-4">
            <button
              onClick={createMask}
              disabled={points.length < 3}
              className={`px-4 py-2 rounded-lg font-medium ${
                points.length < 3
                  ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                  : 'bg-green-500 text-white hover:bg-green-600'
              }`}
            >
              Create Mask
            </button>
            <button
              onClick={resetCurrentMask}
              className="px-4 py-2 bg-gray-500 text-white rounded-lg hover:bg-gray-600"
            >
              Reset
            </button>
          </div>
        </div>
      </div>
    </div>
  );

  const renderStep4 = () => (
    <div className="space-y-6">
      <h3 className="text-xl font-semibold text-gray-900">Step 4: Final Details</h3>
      <p className="text-gray-600">Enter the final details for your mockup.</p>

      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Mockup Name:</label>
          <input
            type="text"
            value={mockupName}
            onChange={e => setMockupName(e.target.value)}
            placeholder="Enter a name for your mockup"
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">Starting Number:</label>
          <input
            type="number"
            min="1"
            value={startingNumber}
            onChange={e => setStartingNumber(parseInt(e.target.value) || 100)}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        {/* Summary */}
        <div className="bg-gray-50 p-4 rounded-lg">
          <h4 className="font-medium text-gray-900 mb-2">Summary:</h4>
          <ul className="text-sm text-gray-600 space-y-1">
            <li>Template: {selectedTemplate?.name}</li>
            <li>Images: {selectedImages.length}</li>
            <li>Total Masks: {Object.values(allMasks).reduce((sum, masks) => sum + Object.keys(masks).length, 0)}</li>
            <li>Name: {mockupName || 'Not set'}</li>
            <li>Starting Number: {startingNumber}</li>
          </ul>
        </div>
      </div>
    </div>
  );

  const renderModalContent = () => {
    switch (currentStep) {
      case 1:
        return renderStep1();
      case 2:
        return renderStep2();
      case 3:
        return renderStep2_5();
      case 4:
        return renderStep3();
      case 5:
        return renderStep4();
      default:
        return null;
    }
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <div className="max-w-6xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-4">Mockup Creator</h1>
          <p className="text-gray-600 mb-6">Create professional mockups with custom masks and templates</p>

          {/* Usage Indicator for Free Tier */}
          {isFreeTier && (
            <div className="max-w-md mx-auto mb-6">
              <UsageIndicator feature={FEATURES.MOCKUP_GENERATOR} size="default" />
            </div>
          )}

          <FeatureGate feature={FEATURES.MOCKUP_GENERATOR} showUpgradePrompt={false}>
            <button
              onClick={startWorkflow}
              disabled={!canCreateMockups}
              className={`px-6 py-3 rounded-lg transition-colors font-medium ${
                canCreateMockups
                  ? 'bg-blue-500 text-white hover:bg-blue-600'
                  : 'bg-gray-300 text-gray-500 cursor-not-allowed'
              }`}
            >
              Add New Base Mockup
              {!canCreateMockups && isFreeTier && <span className="block text-xs mt-1">Monthly limit reached</span>}
            </button>
          </FeatureGate>
        </div>

        {/* Existing Mockups Section */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h2 className="text-2xl font-semibold text-gray-900">Your Mockups</h2>
            <button
              onClick={loadExistingMockups}
              disabled={loadingMockups}
              className="px-3 py-1 text-sm bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
            >
              {loadingMockups ? 'Loading...' : 'Refresh'}
            </button>
          </div>

          {loadingMockups ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading your mockups...</p>
            </div>
          ) : existingMockups.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <div className="text-gray-400 mb-4">
                <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                  />
                </svg>
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No mockups yet</h3>
              <p className="text-gray-600 mb-4">Create your first mockup to get started</p>
              <button
                onClick={startWorkflow}
                className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
              >
                Create Your First Mockup
              </button>
            </div>
          ) : (
            <div className="bg-white shadow-md rounded-lg overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Mockup Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Template Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Starting Name
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Images
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Masks
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {existingMockups.map(mockup => (
                    <tr key={mockup.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {mockup.name || `Mockup #${mockup.id.slice(0, 8)}`}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {mockup.template_name || mockup.product_template_id
                          ? `Template ${mockup.product_template_id}`
                          : 'N/A'}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{mockup.starting_name}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {mockup.mockup_images?.length || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {mockup.mockup_images?.reduce((total, image) => total + (image.mask_data?.length || 0), 0) || 0}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        <div className="flex space-x-2">
                          <button
                            onClick={() => handleViewMockup(mockup)}
                            className="text-blue-600 hover:text-blue-900 px-2 py-1 rounded text-xs"
                          >
                            View
                          </button>
                          <button
                            onClick={() => handleEditMockup(mockup)}
                            className="text-green-600 hover:text-green-900 px-2 py-1 rounded text-xs"
                          >
                            Edit
                          </button>
                          <button
                            onClick={() => handleDeleteMockup(mockup)}
                            className="text-red-600 hover:text-red-900 px-2 py-1 rounded text-xs"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {message && (
          <div
            className={`p-4 rounded-lg mb-6 ${
              message.includes('successfully') ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
            }`}
          >
            {message}
          </div>
        )}
      </div>

      {/* Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="p-6 border-b border-gray-200">
              <div className="flex justify-between items-center">
                <h2 className="text-2xl font-bold text-gray-900">Create Mockups</h2>
                <button onClick={() => setShowModal(false)} className="text-gray-400 hover:text-gray-600">
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              {/* Progress Steps */}
              <div className="flex items-center mt-6 space-x-4">
                {[1, 2, 3, 4, 5].map(step => (
                  <div key={step} className="flex items-center">
                    <div
                      className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                        step <= currentStep ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-600'
                      }`}
                    >
                      {step}
                    </div>
                    {step < 5 && (
                      <div className={`w-12 h-1 mx-2 ${step < currentStep ? 'bg-blue-500' : 'bg-gray-200'}`} />
                    )}
                  </div>
                ))}
              </div>
            </div>

            {/* Content */}
            <div className="p-6">{renderModalContent()}</div>

            {/* Footer */}
            <div className="p-6 border-t border-gray-200 flex justify-between">
              <button
                onClick={goToPreviousStep}
                disabled={currentStep === 1}
                className={`px-4 py-2 rounded-lg font-medium ${
                  currentStep === 1
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-gray-500 text-white hover:bg-gray-600'
                }`}
              >
                Previous
              </button>

              <div className="flex space-x-4">
                {currentStep < 5 ? (
                  <button
                    onClick={goToNextStep}
                    className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 font-medium"
                  >
                    Next
                  </button>
                ) : (
                  <button
                    onClick={createMockup}
                    disabled={loading}
                    className={`px-4 py-2 rounded-lg font-medium ${
                      loading
                        ? 'bg-gray-400 text-white cursor-not-allowed'
                        : 'bg-green-500 text-white hover:bg-green-600'
                    }`}
                  >
                    {loading ? 'Creating...' : 'Create Mockup'}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Action Modals */}
      <ViewMockupModal isOpen={viewModalOpen} onClose={handleModalClose} mockup={selectedMockup} />

      <EditMockupModal
        isOpen={editModalOpen}
        onClose={handleModalClose}
        mockup={selectedMockup}
        onUpdate={handleMockupUpdate}
      />

      <DeleteMockupModal
        isOpen={deleteModalOpen}
        onClose={handleModalClose}
        mockup={selectedMockup}
        onDelete={handleMockupDelete}
      />
    </div>
  );
};

export default MockupCreator;
