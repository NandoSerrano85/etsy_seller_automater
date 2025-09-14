'use client';

import React, { useRef } from 'react';
import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import Button from '@/components/ui/Button';

interface Step2ImagesProps {
  selectedImages: string[];
  handleImageUpload: (e: React.ChangeEvent<HTMLInputElement>) => void;
}

export function Step2Images({ selectedImages, handleImageUpload }: Step2ImagesProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleButtonClick = () => {
    fileInputRef.current?.click();
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Upload Images</h2>
        <p className="text-gray-600">Select the images you want to use in your mockups.</p>
      </div>

      {/* File Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle>Choose Images</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Hidden file input */}
            <Input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              multiple
              onChange={handleImageUpload}
              className="hidden"
              id="image-upload"
            />

            {/* Upload Area */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-gray-400 transition-colors">
              <div className="space-y-4">
                <svg
                  className="mx-auto h-12 w-12 text-gray-400"
                  stroke="currentColor"
                  fill="none"
                  viewBox="0 0 48 48"
                  aria-hidden="true"
                >
                  <path
                    d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02"
                    strokeWidth={2}
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>

                <div>
                  <Button
                    type="button"
                    onClick={handleButtonClick}
                    variant="secondary"
                    className="mb-2"
                  >
                    Choose Images
                  </Button>
                  <p className="text-sm text-gray-500">
                    or drag and drop files here
                  </p>
                </div>

                <div className="text-xs text-gray-400">
                  <p>PNG, JPG, GIF up to 10MB each</p>
                  <p>Multiple files supported</p>
                </div>
              </div>
            </div>

            {/* Upload Stats */}
            {selectedImages.length > 0 && (
              <div className="flex items-center justify-between text-sm text-gray-600">
                <span>{selectedImages.length} image{selectedImages.length !== 1 ? 's' : ''} selected</span>
                <Button
                  type="button"
                  onClick={handleButtonClick}
                  variant="secondary"
                  className="text-xs px-3 py-1"
                >
                  Add More
                </Button>
              </div>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Selected Images Grid */}
      {selectedImages.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle>Selected Images ({selectedImages.length})</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 xl:grid-cols-6 gap-4">
              {selectedImages.map((imageUrl, index) => (
                <div
                  key={index}
                  className="relative group aspect-square bg-gray-100 rounded-lg overflow-hidden border border-gray-200 hover:border-gray-300 transition-colors"
                >
                  <Image
                    src={imageUrl}
                    alt={`Selected image ${index + 1}`}
                    fill
                    className="object-cover"
                    sizes="(max-width: 640px) 50vw, (max-width: 768px) 33vw, (max-width: 1024px) 25vw, (max-width: 1280px) 20vw, 16vw"
                  />

                  {/* Image overlay with index */}
                  <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-opacity flex items-center justify-center">
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                      <div className="w-8 h-8 bg-white bg-opacity-90 rounded-full flex items-center justify-center">
                        <span className="text-xs font-medium text-gray-900">
                          {index + 1}
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Image info tooltip on hover */}
                  <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <p className="truncate">Image {index + 1}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Empty State */}
      {selectedImages.length === 0 && (
        <div className="text-center py-12">
          <div className="mx-auto max-w-sm">
            <svg
              className="mx-auto h-12 w-12 text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
              aria-hidden="true"
            >
              <path
                vectorEffect="non-scaling-stroke"
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No images selected</h3>
            <p className="mt-1 text-sm text-gray-500">
              Choose images to get started with your mockup creation.
            </p>
            <div className="mt-4">
              <Button
                type="button"
                onClick={handleButtonClick}
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
                <span>Upload Images</span>
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}