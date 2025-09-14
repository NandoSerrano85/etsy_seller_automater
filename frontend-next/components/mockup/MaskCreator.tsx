'use client';

import React, { useState, useRef } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/Dialog';
import { Slider } from '@/components/ui/Slider';
import Button from '@/components/ui/Button';
import { useMockupStore } from '@/store/useMockupStore';

interface MaskCreatorProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

interface MaskData {
  name: string;
  file: File;
  adjustments: {
    scale: number;
    rotation: number;
    opacity: number;
  };
}

export function MaskCreator({ open, onOpenChange }: MaskCreatorProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [maskData, setMaskData] = useState<MaskData>({
    name: '',
    file: null as any,
    adjustments: {
      scale: 100,
      rotation: 0,
      opacity: 100,
    },
  });

  const fileInputRef = useRef<HTMLInputElement>(null);
  const { addMask } = useMockupStore();

  const steps = [
    'Upload Mask Shape',
    'Adjust Mask Area',
    'Confirm and Apply'
  ];

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setMaskData(prev => ({
        ...prev,
        file,
        name: file.name.replace(/\.[^/.]+$/, '') // Remove file extension
      }));
    }
  };

  const handleAdjustmentChange = (field: keyof MaskData['adjustments']) => (value: number[]) => {
    setMaskData(prev => ({
      ...prev,
      adjustments: {
        ...prev.adjustments,
        [field]: value[0]
      }
    }));
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleFinish = () => {
    if (maskData.file) {
      addMask({
        file: maskData.file,
        settings: {
          name: maskData.name,
          adjustments: maskData.adjustments,
        },
      });
      resetModal();
      onOpenChange(false);
    }
  };

  const resetModal = () => {
    setCurrentStep(0);
    setMaskData({
      name: '',
      file: null as any,
      adjustments: {
        scale: 100,
        rotation: 0,
        opacity: 100,
      },
    });
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClose = () => {
    resetModal();
    onOpenChange(false);
  };

  const isNextDisabled = currentStep === 0 && !maskData.file;
  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  const renderStepContent = () => {
    switch (currentStep) {
      case 0:
        return (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Upload a mask shape file to define the printable area for your mockup.
            </p>

            <div className="border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*,.svg"
                onChange={handleFileChange}
                className="hidden"
                id="mask-file-input"
                aria-describedby="file-upload-description"
              />

              <div className="space-y-3">
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

                {maskData.file ? (
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      {maskData.file.name}
                    </p>
                    <p className="text-xs text-gray-500">
                      {(maskData.file.size / 1024).toFixed(1)} KB
                    </p>
                  </div>
                ) : (
                  <div>
                    <p className="text-sm text-gray-600">
                      Click to upload or drag and drop
                    </p>
                    <p className="text-xs text-gray-500" id="file-upload-description">
                      PNG, JPG, SVG up to 10MB
                    </p>
                  </div>
                )}

                <label htmlFor="mask-file-input">
                  <Button
                    type="button"
                    variant="secondary"
                    className="cursor-pointer"
                    onClick={() => fileInputRef.current?.click()}
                  >
                    {maskData.file ? 'Change File' : 'Choose File'}
                  </Button>
                </label>
              </div>
            </div>

            {maskData.file && (
              <div className="space-y-2">
                <label
                  htmlFor="mask-name"
                  className="block text-sm font-medium text-gray-700"
                >
                  Mask Name
                </label>
                <input
                  id="mask-name"
                  type="text"
                  value={maskData.name}
                  onChange={(e) => setMaskData(prev => ({ ...prev, name: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary"
                  placeholder="Enter mask name"
                />
              </div>
            )}
          </div>
        );

      case 1:
        return (
          <div className="space-y-6">
            <p className="text-sm text-gray-600">
              Adjust the mask properties to fit your mockup requirements.
            </p>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Scale: {maskData.adjustments.scale}%
                </label>
                <Slider
                  value={[maskData.adjustments.scale]}
                  min={10}
                  max={200}
                  step={5}
                  onValueChange={handleAdjustmentChange('scale')}
                  aria-label="Mask scale adjustment"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Rotation: {maskData.adjustments.rotation}°
                </label>
                <Slider
                  value={[maskData.adjustments.rotation]}
                  min={-180}
                  max={180}
                  step={1}
                  onValueChange={handleAdjustmentChange('rotation')}
                  aria-label="Mask rotation adjustment"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Opacity: {maskData.adjustments.opacity}%
                </label>
                <Slider
                  value={[maskData.adjustments.opacity]}
                  min={0}
                  max={100}
                  step={5}
                  onValueChange={handleAdjustmentChange('opacity')}
                  aria-label="Mask opacity adjustment"
                />
              </div>
            </div>

            {maskData.file && (
              <div className="bg-gray-50 p-4 rounded-md">
                <h4 className="text-sm font-medium text-gray-900 mb-2">Preview</h4>
                <div className="text-xs text-gray-600">
                  <p>File: {maskData.file.name}</p>
                  <p>Scale: {maskData.adjustments.scale}%</p>
                  <p>Rotation: {maskData.adjustments.rotation}°</p>
                  <p>Opacity: {maskData.adjustments.opacity}%</p>
                </div>
              </div>
            )}
          </div>
        );

      case 2:
        return (
          <div className="space-y-4">
            <p className="text-sm text-gray-600">
              Review your mask settings and confirm to add it to your mockup collection.
            </p>

            <div className="bg-gray-50 p-4 rounded-md space-y-3">
              <div>
                <h4 className="text-sm font-medium text-gray-900">Mask Details</h4>
              </div>

              <div className="grid grid-cols-2 gap-4 text-xs">
                <div>
                  <span className="text-gray-500">Name:</span>
                  <p className="font-medium">{maskData.name}</p>
                </div>
                <div>
                  <span className="text-gray-500">File:</span>
                  <p className="font-medium">{maskData.file?.name}</p>
                </div>
                <div>
                  <span className="text-gray-500">Scale:</span>
                  <p className="font-medium">{maskData.adjustments.scale}%</p>
                </div>
                <div>
                  <span className="text-gray-500">Rotation:</span>
                  <p className="font-medium">{maskData.adjustments.rotation}°</p>
                </div>
                <div>
                  <span className="text-gray-500">Opacity:</span>
                  <p className="font-medium">{maskData.adjustments.opacity}%</p>
                </div>
                <div>
                  <span className="text-gray-500">Size:</span>
                  <p className="font-medium">{maskData.file ? (maskData.file.size / 1024).toFixed(1) + ' KB' : 'N/A'}</p>
                </div>
              </div>
            </div>

            <div className="bg-blue-50 p-3 rounded-md">
              <p className="text-xs text-blue-800">
                ℹ️ This mask will be added to your mockup collection and can be applied to products.
              </p>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleClose}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Create Mask</DialogTitle>
          <div className="mt-2">
            <div className="flex items-center justify-between text-sm text-gray-500">
              <span>Step {currentStep + 1} of {steps.length}</span>
              <span>{steps[currentStep]}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-1 mt-2">
              <div
                className="bg-primary h-1 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
                role="progressbar"
                aria-valuenow={currentStep + 1}
                aria-valuemin={1}
                aria-valuemax={steps.length}
                aria-label={`Step ${currentStep + 1} of ${steps.length}: ${steps[currentStep]}`}
              />
            </div>
          </div>
        </DialogHeader>

        <div className="py-4 min-h-[300px]">
          {renderStepContent()}
        </div>

        <div className="flex items-center justify-between pt-4 border-t">
          <Button
            variant="secondary"
            onClick={handleBack}
            disabled={isFirstStep}
          >
            Back
          </Button>

          <div className="flex space-x-2">
            <Button
              variant="secondary"
              onClick={handleClose}
            >
              Cancel
            </Button>

            {isLastStep ? (
              <Button
                onClick={handleFinish}
                disabled={!maskData.file}
              >
                Finish
              </Button>
            ) : (
              <Button
                onClick={handleNext}
                disabled={isNextDisabled}
              >
                Next
              </Button>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}