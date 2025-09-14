'use client';

import React, { useRef } from 'react';
import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';

interface Step2ImagesProps {
  selectedImages: string[];
  imageFiles: File[];
  watermarkFile: File | null;
  onImageUpload: (files: FileList) => void;
  onWatermarkUpload: (file: File) => void;
  onRemoveImage: (index: number) => void;
  onRemoveWatermark: () => void;
}

export function Step2Images({
  selectedImages,
  imageFiles,
  watermarkFile,
  onImageUpload,
  onWatermarkUpload,
  onRemoveImage,
  onRemoveWatermark
}: Step2ImagesProps) {
  const imageInputRef = useRef<HTMLInputElement>(null);
  const watermarkInputRef = useRef<HTMLInputElement>(null);

  const handleImageChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      onImageUpload(files);
    }
  };

  const handleWatermarkChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      onWatermarkUpload(file);
    }
  };

  return (
    <div className="space-y-6">
      {/* Main Images */}
      <Card>
        <CardHeader>
          <CardTitle>Upload Images</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                ref={imageInputRef}
                type="file"
                accept="image/*"
                multiple
                onChange={handleImageChange}
                className="hidden"
              />

              <svg
                className="mx-auto h-12 w-12 text-gray-400"
                stroke="currentColor"
                fill="none"
                viewBox="0 0 48 48"
              >
                <path
                  d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                  strokeWidth={2}
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>

              <div className="mt-4">
                <Button
                  onClick={() => imageInputRef.current?.click()}
                  variant="secondary"
                >
                  Choose Images
                </Button>
                <p className="mt-2 text-sm text-gray-500">
                  PNG, JPG, GIF up to 10MB each
                </p>
              </div>
            </div>

            {selectedImages.length > 0 && (
              <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-4">
                {selectedImages.map((image, index) => (
                  <div key={index} className="relative group">
                    <div className="aspect-square bg-gray-100 rounded-lg relative overflow-hidden">
                      <Image
                        src={image}
                        alt={`Uploaded image ${index + 1}`}
                        fill
                        className="object-cover"
                      />
                    </div>
                    <button
                      onClick={() => onRemoveImage(index)}
                      className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 text-white rounded-full opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-xs"
                    >
                      ×
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Watermark */}
      <Card>
        <CardHeader>
          <CardTitle>Watermark (Optional)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center">
              <input
                ref={watermarkInputRef}
                type="file"
                accept="image/*"
                onChange={handleWatermarkChange}
                className="hidden"
              />

              {watermarkFile ? (
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-gray-100 rounded relative overflow-hidden">
                      <Image
                        src={URL.createObjectURL(watermarkFile)}
                        alt="Watermark"
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div className="text-left">
                      <p className="text-sm font-medium">{watermarkFile.name}</p>
                      <p className="text-xs text-gray-500">
                        {(watermarkFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                  <Button
                    onClick={onRemoveWatermark}
                    variant="destructive"
                    className="text-xs px-2 py-1"
                  >
                    Remove
                  </Button>
                </div>
              ) : (
                <div>
                  <Button
                    onClick={() => watermarkInputRef.current?.click()}
                    variant="secondary"
                  >
                    Upload Watermark
                  </Button>
                  <p className="mt-2 text-sm text-gray-500">
                    PNG with transparency recommended
                  </p>
                </div>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}