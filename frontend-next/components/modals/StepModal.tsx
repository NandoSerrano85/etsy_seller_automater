'use client';

import { useState, useEffect } from 'react';

interface StepModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  steps: React.ReactNode[];
  title?: string;
}

export default function StepModal({ open, onOpenChange, steps, title }: StepModalProps) {
  const [currentStep, setCurrentStep] = useState<number>(0);

  useEffect(() => {
    if (!open) {
      setCurrentStep(0);
    }
  }, [open]);

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleFinish = () => {
    onOpenChange(false);
  };

  const isFirstStep = currentStep === 0;
  const isLastStep = currentStep === steps.length - 1;

  if (!open) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full mx-4">
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-semibold text-gray-900">
            {title || 'Step Modal'}
          </h2>
          <button
            onClick={() => onOpenChange(false)}
            className="text-gray-400 hover:text-gray-600"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>

        <div className="p-6">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm text-gray-500">
                Step {currentStep + 1} of {steps.length}
              </span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary h-2 rounded-full transition-all duration-300"
                style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
              ></div>
            </div>
          </div>

          <div className="min-h-[200px]">
            {steps[currentStep]}
          </div>
        </div>

        <div className="flex items-center justify-between p-6 border-t bg-gray-50">
          <button
            onClick={handleBack}
            disabled={isFirstStep}
            className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Back
          </button>

          <div className="flex space-x-2">
            {isLastStep ? (
              <button
                onClick={handleFinish}
                className="px-4 py-2 text-sm font-medium text-white bg-primary border border-transparent rounded-md hover:bg-opacity-90"
              >
                Finish
              </button>
            ) : (
              <button
                onClick={handleNext}
                className="px-4 py-2 text-sm font-medium text-white bg-primary border border-transparent rounded-md hover:bg-opacity-90"
              >
                Next
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}