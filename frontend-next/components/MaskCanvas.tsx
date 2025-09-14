'use client';

import { useRef, useEffect, useState, useCallback, forwardRef, useImperativeHandle } from 'react';

interface Rectangle {
  id: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

interface MaskCanvasProps {
  imageSrc?: string;
  onSave?: (masks: Rectangle[]) => void;
}

export interface MaskCanvasRef {
  getMasks: () => Rectangle[];
}

const MaskCanvas = forwardRef<MaskCanvasRef, MaskCanvasProps>(({ imageSrc, onSave }, ref) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [isDrawing, setIsDrawing] = useState<boolean>(false);
  const [currentRect, setCurrentRect] = useState<Rectangle | null>(null);
  const [rectangles, setRectangles] = useState<Rectangle[]>([]);
  const [startPoint, setStartPoint] = useState<{ x: number; y: number } | null>(null);

  useImperativeHandle(ref, () => ({
    getMasks: () => rectangles,
  }));

  const drawCanvas = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Clear canvas
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Draw background image if provided
    if (imageSrc) {
      const img = new Image();
      img.onload = () => {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        drawRectangles(ctx);
      };
      img.src = imageSrc;
    } else {
      // Draw placeholder background
      ctx.fillStyle = '#f3f4f6';
      ctx.fillRect(0, 0, canvas.width, canvas.height);
      drawRectangles(ctx);
    }
  }, [imageSrc, rectangles, currentRect]);

  const drawRectangles = (ctx: CanvasRenderingContext2D) => {
    // Draw existing rectangles
    rectangles.forEach((rect) => {
      ctx.strokeStyle = '#3b82f6';
      ctx.lineWidth = 2;
      ctx.strokeRect(rect.x, rect.y, rect.width, rect.height);
      ctx.fillStyle = 'rgba(59, 130, 246, 0.1)';
      ctx.fillRect(rect.x, rect.y, rect.width, rect.height);
    });

    // Draw current rectangle being drawn
    if (currentRect) {
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
      ctx.setLineDash([5, 5]);
      ctx.strokeRect(currentRect.x, currentRect.y, currentRect.width, currentRect.height);
      ctx.fillStyle = 'rgba(239, 68, 68, 0.1)';
      ctx.fillRect(currentRect.x, currentRect.y, currentRect.width, currentRect.height);
      ctx.setLineDash([]);
    }
  };

  useEffect(() => {
    drawCanvas();
  }, [drawCanvas]);

  const getCanvasCoordinates = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const canvas = canvasRef.current;
    if (!canvas) return { x: 0, y: 0 };

    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  };

  const handleMouseDown = (event: React.MouseEvent<HTMLCanvasElement>) => {
    const coords = getCanvasCoordinates(event);
    setIsDrawing(true);
    setStartPoint(coords);
    setCurrentRect({
      id: Date.now().toString(),
      x: coords.x,
      y: coords.y,
      width: 0,
      height: 0,
    });
  };

  const handleMouseMove = (event: React.MouseEvent<HTMLCanvasElement>) => {
    if (!isDrawing || !startPoint) return;

    const coords = getCanvasCoordinates(event);
    const width = coords.x - startPoint.x;
    const height = coords.y - startPoint.y;

    setCurrentRect({
      id: Date.now().toString(),
      x: width < 0 ? coords.x : startPoint.x,
      y: height < 0 ? coords.y : startPoint.y,
      width: Math.abs(width),
      height: Math.abs(height),
    });
  };

  const handleMouseUp = () => {
    if (!isDrawing || !currentRect || currentRect.width < 10 || currentRect.height < 10) {
      setIsDrawing(false);
      setCurrentRect(null);
      setStartPoint(null);
      return;
    }

    setRectangles((prev) => [...prev, currentRect]);
    setIsDrawing(false);
    setCurrentRect(null);
    setStartPoint(null);

    if (onSave) {
      onSave([...rectangles, currentRect]);
    }
  };

  const handleClear = () => {
    setRectangles([]);
    setCurrentRect(null);
    if (onSave) {
      onSave([]);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-medium text-gray-900">Mask Canvas</h3>
        <div className="flex space-x-2">
          <button
            onClick={handleClear}
            className="px-3 py-1 text-sm bg-gray-500 text-white rounded hover:bg-gray-600"
          >
            Clear
          </button>
          <span className="text-sm text-gray-500">
            Masks: {rectangles.length}
          </span>
        </div>
      </div>

      <div className="border border-gray-300 rounded-lg overflow-hidden">
        <canvas
          ref={canvasRef}
          width={600}
          height={400}
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          className="cursor-crosshair bg-white block"
        />
      </div>

      <p className="text-sm text-gray-600">
        Click and drag to create rectangular masks. Minimum size: 10x10 pixels.
      </p>
    </div>
  );
});

MaskCanvas.displayName = 'MaskCanvas';

export default MaskCanvas;