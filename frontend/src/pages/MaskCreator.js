import React, { useState, useRef, useEffect } from 'react';
import { useApi } from '../hooks/useApi';

const MaskCreator = () => {
  const api = useApi();
  const [mockupImage, setMockupImage] = useState(null);
  const [points, setPoints] = useState([]);
  const [drawingMode, setDrawingMode] = useState('point'); // 'point' or 'rectangle'
  const [rectStart, setRectStart] = useState(null);
  const [masks, setMasks] = useState([]);
  const [currentMaskIndex, setCurrentMaskIndex] = useState(0);
  const [numMasks, setNumMasks] = useState(1);
  const [isDrawing, setIsDrawing] = useState(false);
  const canvasRef = useRef(null);
  const [scaleFactor, setScaleFactor] = useState(1.0);

  const handleImageUpload = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const img = new Image();
        img.onload = () => {
          setMockupImage(img);
          // Calculate scale factor for display
          const maxSize = 1200;
          const scale = Math.min(maxSize / img.width, maxSize / img.height);
          setScaleFactor(scale);
        };
        img.src = e.target.result;
      };
      reader.readAsDataURL(file);
    }
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

  const getMousePos = (event) => {
    const canvas = canvasRef.current;
    if (!canvas) return null;

    const rect = canvas.getBoundingClientRect();
    return {
      x: (event.clientX - rect.left) * (canvas.width / rect.width),
      y: (event.clientY - rect.top) * (canvas.height / rect.height)
    };
  };

  const handleCanvasClick = (event) => {
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
        const rectPoints = [
          rectStart,
          { x: mousePos.x, y: rectStart.y },
          mousePos,
          { x: rectStart.x, y: mousePos.y }
        ];
        setPoints(rectPoints);
        setRectStart(null);
      }
    }
  };

  const handleCanvasMouseMove = (event) => {
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
      alert('Need at least 3 points to create a mask');
      return;
    }

    // Scale points back to original image size
    const scaledPoints = points.map(point => ({
      x: point.x / scaleFactor,
      y: point.y / scaleFactor
    }));

    const newMask = {
      points: scaledPoints,
      displayPoints: [...points]
    };

    setMasks([...masks, newMask]);
    setPoints([]);
    setRectStart(null);
    setCurrentMaskIndex(currentMaskIndex + 1);

    if (currentMaskIndex + 1 >= numMasks) {
      // All masks created
      saveMasks();
    }
  };

  const resetCurrentMask = () => {
    setPoints([]);
    setRectStart(null);
  };

  const saveMasks = async () => {
    try {
      await api.post('/api/masks', {
        masks: masks.map(mask => mask.points),
        imageType: 'UVDTF 16oz'
      });

      alert('Masks saved successfully!');
      // Reset for next use
      setMasks([]);
      setCurrentMaskIndex(0);
      setPoints([]);
    } catch (error) {
      console.error('Error saving masks:', error);
      alert('Error saving masks');
    }
  };

  const setMode = (mode) => {
    setDrawingMode(mode);
    setPoints([]);
    setRectStart(null);
  };

  useEffect(() => {
    drawImage();
  }, [mockupImage, points, masks, currentMaskIndex, rectStart]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600 py-8">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center text-white mb-8">
          <h1 className="text-4xl font-bold mb-4">Mask Creator</h1>
          <p className="text-xl opacity-90">Create masks for mockup images by drawing polygons or rectangles</p>
        </div>

        {/* Controls */}
        <div className="card p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="space-y-2">
              <label htmlFor="image-upload" className="block text-sm font-medium text-gray-700">
                Upload Mockup Image:
              </label>
              <input
                id="image-upload"
                type="file"
                accept="image/*"
                onChange={handleImageUpload}
                className="input-field"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="num-masks" className="block text-sm font-medium text-gray-700">
                Number of Masks:
              </label>
              <select
                id="num-masks"
                value={numMasks}
                onChange={(e) => setNumMasks(parseInt(e.target.value))}
                className="input-field"
              >
                <option value={1}>1</option>
                <option value={2}>2</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-gray-700">Drawing Mode:</label>
              <div className="flex space-x-2">
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    drawingMode === 'point' 
                      ? 'bg-blue-500 text-white' 
                      : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                  }`}
                  onClick={() => setMode('point')}
                >
                  Point Mode
                </button>
                <button
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
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
              <div className="flex space-x-2">
                <button 
                  onClick={createMask} 
                  disabled={points.length < 3}
                  className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                    points.length < 3
                      ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                      : 'bg-green-500 text-white hover:bg-green-600'
                  }`}
                >
                  Create Mask ({currentMaskIndex + 1}/{numMasks})
                </button>
                <button 
                  onClick={resetCurrentMask}
                  className="px-4 py-2 bg-gray-500 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
                >
                  Reset Current
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Canvas */}
        <div className="card p-6 mb-8">
          {mockupImage ? (
            <div className="flex justify-center">
              <canvas
                ref={canvasRef}
                onClick={handleCanvasClick}
                onMouseMove={handleCanvasMouseMove}
                className="border-2 border-gray-300 cursor-crosshair rounded-lg"
              />
            </div>
          ) : (
            <div className="text-center py-12">
              <div className="text-gray-400 mb-4">
                <svg className="mx-auto h-12 w-12" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
              <p className="text-gray-600">Please upload a mockup image to start creating masks</p>
            </div>
          )}
        </div>

        {/* Instructions */}
        <div className="card p-6 mb-8">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Instructions:</h3>
          <ul className="space-y-2 text-gray-600">
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span><strong>Point Mode:</strong> Click to add points, then click "Create Mask" to close the shape</span>
            </li>
            <li className="flex items-start">
              <span className="text-blue-500 mr-2">•</span>
              <span><strong>Rectangle Mode:</strong> Click and drag to create a rectangle</span>
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
              <span>Masks will be automatically saved when all are created</span>
            </li>
          </ul>
        </div>

        {/* Mask Summary */}
        {masks.length > 0 && (
          <div className="card p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Created Masks:</h3>
            <ul className="space-y-2">
              {masks.map((mask, index) => (
                <li key={index} className="flex items-center text-gray-600">
                  <span className="w-6 h-6 bg-blue-500 text-white rounded-full flex items-center justify-center text-sm font-medium mr-3">
                    {index + 1}
                  </span>
                  Mask {index + 1}: {mask.points.length} points
                </li>
              ))}
            </ul>
          </div>
        )}
      </div>
    </div>
  );
};

export default MaskCreator; 