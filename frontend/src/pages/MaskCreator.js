import React, { useState, useRef, useEffect } from 'react';
import './MaskCreator.css';

const MaskCreator = () => {
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
    const { canvas, ctx } = getCanvasContext();
    if (!canvas || !ctx || !mockupImage) return;

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
    const { ctx } = getCanvasContext();
    if (!ctx) return;

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
      const mousePos = getMousePos();
      if (mousePos) {
        ctx.strokeStyle = '#00ffff';
        ctx.lineWidth = 2;
        ctx.setLineDash([5, 5]);
        ctx.strokeRect(rectStart.x, rectStart.y, mousePos.x - rectStart.x, mousePos.y - rectStart.y);
        ctx.setLineDash([]);
      }
    }
  };

  const drawMask = (maskPoints, color) => {
    const { ctx } = getCanvasContext();
    if (!ctx || !maskPoints.length) return;

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

  const getMousePos = () => {
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

    const mousePos = getMousePos();
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
      drawImage();
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
      const response = await fetch('/api/masks', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          masks: masks.map(mask => mask.points),
          imageType: 'UVDTF 16oz'
        }),
      });

      if (response.ok) {
        alert('Masks saved successfully!');
        // Reset for next use
        setMasks([]);
        setCurrentMaskIndex(0);
        setPoints([]);
      } else {
        alert('Failed to save masks');
      }
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
    <div className="mask-creator">
      <div className="mask-creator-header">
        <h1>Mask Creator</h1>
        <p>Create masks for mockup images by drawing polygons or rectangles</p>
      </div>

      <div className="mask-creator-controls">
        <div className="control-group">
          <label htmlFor="image-upload">Upload Mockup Image:</label>
          <input
            id="image-upload"
            type="file"
            accept="image/*"
            onChange={handleImageUpload}
          />
        </div>

        <div className="control-group">
          <label htmlFor="num-masks">Number of Masks:</label>
          <select
            id="num-masks"
            value={numMasks}
            onChange={(e) => setNumMasks(parseInt(e.target.value))}
          >
            <option value={1}>1</option>
            <option value={2}>2</option>
          </select>
        </div>

        <div className="control-group">
          <label>Drawing Mode:</label>
          <div className="mode-buttons">
            <button
              className={drawingMode === 'point' ? 'active' : ''}
              onClick={() => setMode('point')}
            >
              Point Mode
            </button>
            <button
              className={drawingMode === 'rectangle' ? 'active' : ''}
              onClick={() => setMode('rectangle')}
            >
              Rectangle Mode
            </button>
          </div>
        </div>

        <div className="control-group">
          <label>Actions:</label>
          <div className="action-buttons">
            <button onClick={createMask} disabled={points.length < 3}>
              Create Mask ({currentMaskIndex + 1}/{numMasks})
            </button>
            <button onClick={resetCurrentMask}>
              Reset Current
            </button>
          </div>
        </div>
      </div>

      <div className="mask-creator-canvas">
        {mockupImage ? (
          <canvas
            ref={canvasRef}
            onClick={handleCanvasClick}
            onMouseMove={handleCanvasMouseMove}
            style={{ border: '2px solid #ccc', cursor: 'crosshair' }}
          />
        ) : (
          <div className="upload-prompt">
            <p>Please upload a mockup image to start creating masks</p>
          </div>
        )}
      </div>

      <div className="mask-creator-instructions">
        <h3>Instructions:</h3>
        <ul>
          <li><strong>Point Mode:</strong> Click to add points, then click "Create Mask" to close the shape</li>
          <li><strong>Rectangle Mode:</strong> Click and drag to create a rectangle</li>
          <li>You need at least 3 points to create a mask</li>
          <li>Use "Reset Current" to start over with the current mask</li>
          <li>Masks will be automatically saved when all are created</li>
        </ul>
      </div>

      {masks.length > 0 && (
        <div className="mask-summary">
          <h3>Created Masks:</h3>
          <ul>
            {masks.map((mask, index) => (
              <li key={index}>
                Mask {index + 1}: {mask.points.length} points
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MaskCreator; 