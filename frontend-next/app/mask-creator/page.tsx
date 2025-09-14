'use client';

import { useState, useRef } from 'react';
import MaskCanvas from '@/components/MaskCanvas';

interface Mask {
  id: string;
  name: string;
  data: string;
}

export default function MaskCreatorPage() {
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');
  const maskCanvasRef = useRef<any>(null);

  const handleSave = async () => {
    setLoading(true);
    setMessage('');

    try {
      // Get masks from the MaskCanvas component
      const masks = maskCanvasRef.current?.getMasks() || [];

      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/masks`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            masks: masks,
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMessage(
          `Masks saved successfully! ${result.count || masks.length} mask(s) saved.`
        );
      } else {
        setMessage('Failed to save masks. Please try again.');
      }
    } catch (error) {
      console.error('Error saving masks:', error);
      setMessage('Error saving masks. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Mask Creator</h1>

      <div className="mb-6">
        <MaskCanvas ref={maskCanvasRef} />
      </div>

      <div className="flex items-center gap-4">
        <button
          onClick={handleSave}
          disabled={loading}
          className="bg-primary text-white px-6 py-3 rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50"
        >
          {loading ? 'Saving...' : 'Save Masks'}
        </button>

        {message && (
          <div
            className={`p-3 rounded-md ${
              message.includes('successfully')
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
