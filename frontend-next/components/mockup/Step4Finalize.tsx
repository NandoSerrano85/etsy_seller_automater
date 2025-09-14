'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import Button from '@/components/ui/Button';

interface Template {
  id: string;
  name: string;
  thumbnail: string;
  category: string;
}

interface Step4FinalizeProps {
  selectedTemplate: Template | null;
  selectedImages: string[];
  watermarkFile: File | null;
  allMasks: Record<string, any>;
  mockupName: string;
  startingNumber: number;
  onMockupNameChange: (name: string) => void;
  onStartingNumberChange: (number: number) => void;
  onPreview: () => void;
  onGenerate: () => void;
  isGenerating: boolean;
}

export function Step4Finalize({
  selectedTemplate,
  selectedImages,
  watermarkFile,
  allMasks,
  mockupName,
  startingNumber,
  onMockupNameChange,
  onStartingNumberChange,
  onPreview,
  onGenerate,
  isGenerating
}: Step4FinalizeProps) {
  const totalMasks = Object.values(allMasks).reduce(
    (total: number, imageMasks: any) => total + Object.keys(imageMasks).length,
    0
  );

  return (
    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle>Mockup Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="space-y-4">
              {/* Template */}
              {selectedTemplate && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Template</h4>
                  <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                    <div className="w-12 h-12 bg-gray-100 rounded relative overflow-hidden">
                      <Image
                        src={selectedTemplate.thumbnail || '/placeholder-template.png'}
                        alt={selectedTemplate.name}
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{selectedTemplate.name}</p>
                      <p className="text-sm text-gray-500">{selectedTemplate.category}</p>
                    </div>
                  </div>
                </div>
              )}

              {/* Images */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Images ({selectedImages.length})
                </h4>
                <div className="grid grid-cols-4 gap-2">
                  {selectedImages.slice(0, 4).map((image, index) => (
                    <div key={index} className="aspect-square bg-gray-100 rounded relative overflow-hidden">
                      <Image
                        src={image}
                        alt={`Image ${index + 1}`}
                        fill
                        className="object-cover"
                      />
                    </div>
                  ))}
                  {selectedImages.length > 4 && (
                    <div className="aspect-square bg-gray-100 rounded flex items-center justify-center">
                      <span className="text-sm text-gray-500">+{selectedImages.length - 4}</span>
                    </div>
                  )}
                </div>
              </div>

              {/* Watermark */}
              {watermarkFile && (
                <div>
                  <h4 className="text-sm font-medium text-gray-900 mb-2">Watermark</h4>
                  <div className="flex items-center space-x-3 p-3 border border-gray-200 rounded-lg">
                    <div className="w-12 h-12 bg-gray-100 rounded relative overflow-hidden">
                      <Image
                        src={URL.createObjectURL(watermarkFile)}
                        alt="Watermark"
                        fill
                        className="object-cover"
                      />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">{watermarkFile.name}</p>
                      <p className="text-sm text-gray-500">
                        {(watermarkFile.size / 1024).toFixed(1)} KB
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-4">
              {/* Masks Summary */}
              <div>
                <h4 className="text-sm font-medium text-gray-900 mb-2">
                  Masks ({totalMasks} total)
                </h4>
                <div className="space-y-2">
                  {Object.entries(allMasks).map(([imageIndex, masks]: [string, any]) => {
                    const maskCount = Object.keys(masks).length;
                    return maskCount > 0 ? (
                      <div key={imageIndex} className="flex justify-between text-sm p-2 bg-gray-50 rounded">
                        <span>Image {parseInt(imageIndex) + 1}</span>
                        <span className="font-medium">{maskCount} mask{maskCount !== 1 ? 's' : ''}</span>
                      </div>
                    ) : null;
                  })}
                  {totalMasks === 0 && (
                    <p className="text-sm text-gray-500 italic">No masks created</p>
                  )}
                </div>
              </div>

              {/* Settings */}
              <div className="space-y-3">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Mockup Name
                  </label>
                  <Input
                    value={mockupName}
                    onChange={(e) => onMockupNameChange(e.target.value)}
                    placeholder="Enter mockup name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">
                    Starting Number
                  </label>
                  <Input
                    type="number"
                    value={startingNumber}
                    onChange={(e) => onStartingNumberChange(parseInt(e.target.value) || 1)}
                    min={1}
                  />
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions */}
      <Card>
        <CardHeader>
          <CardTitle>Generate Mockups</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-between">
            <div className="text-sm text-gray-600">
              <p>Ready to generate {selectedImages.length} mockup{selectedImages.length !== 1 ? 's' : ''}</p>
              {totalMasks > 0 && (
                <p>Using {totalMasks} custom mask{totalMasks !== 1 ? 's' : ''}</p>
              )}
            </div>

            <div className="flex space-x-3">
              <Button
                onClick={onPreview}
                variant="secondary"
                disabled={isGenerating || !selectedTemplate || selectedImages.length === 0}
              >
                Preview
              </Button>
              <Button
                onClick={onGenerate}
                disabled={isGenerating || !selectedTemplate || selectedImages.length === 0}
                className="min-w-[120px]"
              >
                {isGenerating ? 'Generating...' : 'Generate Mockups'}
              </Button>
            </div>
          </div>

          {(!selectedTemplate || selectedImages.length === 0) && (
            <div className="mt-4 p-3 bg-amber-50 border border-amber-200 rounded">
              <p className="text-sm text-amber-800">
                Please complete the previous steps before generating mockups.
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}