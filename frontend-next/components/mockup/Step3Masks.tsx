'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';
import { MaskCreator } from './MaskCreator';

interface Step3MasksProps {
  currentImageIndex: number;
  currentMaskIndex: number;
  selectedImages: string[];
  allMasks: Record<string, any>;
  onImageSelect: (index: number) => void;
  onPrevMask: () => void;
  onNextMask: () => void;
  onCreateMask: () => void;
  onDeleteMask: () => void;
  maskModalOpen: boolean;
  setMaskModalOpen: (open: boolean) => void;
}

export function Step3Masks({
  currentImageIndex,
  currentMaskIndex,
  selectedImages,
  allMasks,
  onImageSelect,
  onPrevMask,
  onNextMask,
  onCreateMask,
  onDeleteMask,
  maskModalOpen,
  setMaskModalOpen
}: Step3MasksProps) {
  const currentImageMasks = allMasks[currentImageIndex] || {};
  const maskCount = Object.keys(currentImageMasks).length;

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Create Masks</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Image Selection */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Select Image ({currentImageIndex + 1} of {selectedImages.length})
              </label>
              <div className="flex space-x-2 overflow-x-auto pb-2">
                {selectedImages.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => onImageSelect(index)}
                    className={`flex-shrink-0 w-16 h-16 rounded border-2 relative overflow-hidden ${
                      currentImageIndex === index
                        ? 'border-primary'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <img
                      src={image}
                      alt={`Image ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            </div>

            {/* Canvas Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 bg-gray-50">
              <div className="text-center">
                <div className="w-96 h-64 mx-auto bg-white border rounded-lg shadow-sm flex items-center justify-center">
                  {selectedImages[currentImageIndex] ? (
                    <img
                      src={selectedImages[currentImageIndex]}
                      alt="Current image"
                      className="max-w-full max-h-full object-contain"
                    />
                  ) : (
                    <div className="text-gray-500">
                      <p>No image selected</p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Mask Controls */}
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-4">
                <span className="text-sm text-gray-600">
                  Mask {currentMaskIndex + 1} of {Math.max(maskCount, 1)}
                </span>
                <div className="flex space-x-2">
                  <Button
                    onClick={onPrevMask}
                    disabled={currentMaskIndex === 0}
                    variant="secondary"
                    className="px-2 py-1 text-xs"
                  >
                    ← Prev
                  </Button>
                  <Button
                    onClick={onNextMask}
                    disabled={currentMaskIndex >= maskCount - 1}
                    variant="secondary"
                    className="px-2 py-1 text-xs"
                  >
                    Next →
                  </Button>
                </div>
              </div>

              <div className="flex space-x-2">
                <Button
                  onClick={onCreateMask}
                  className="flex items-center space-x-2"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                    />
                  </svg>
                  <span>Create Mask</span>
                </Button>

                {maskCount > 0 && (
                  <Button
                    onClick={onDeleteMask}
                    variant="destructive"
                    className="flex items-center space-x-2"
                  >
                    <svg
                      className="w-4 h-4"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                      />
                    </svg>
                    <span>Delete</span>
                  </Button>
                )}
              </div>
            </div>

            {/* Mask Info */}
            {maskCount > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h4 className="font-medium text-blue-900 mb-2">Current Mask Info</h4>
                <div className="text-sm text-blue-800">
                  <p>Total masks for this image: {maskCount}</p>
                  <p>Current mask: {currentMaskIndex + 1}</p>
                </div>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* MaskCreator Modal */}
      <MaskCreator
        open={maskModalOpen}
        onOpenChange={setMaskModalOpen}
      />
    </div>
  );
}