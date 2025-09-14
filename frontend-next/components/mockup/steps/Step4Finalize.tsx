'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import { Input } from '@/components/ui/Input';
import Button from '@/components/ui/Button';

interface Step4FinalizeProps {
  mockupName: string;
  setMockupName: (s: string) => void;
  startingNumber: number;
  setStartingNumber: (n: number) => void;
}

export function Step4Finalize({
  mockupName,
  setMockupName,
  startingNumber,
  setStartingNumber
}: Step4FinalizeProps) {
  const handleNameChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setMockupName(e.target.value);
  };

  const handleNumberChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = parseInt(e.target.value, 10);
    if (!isNaN(value) && value > 0) {
      setStartingNumber(value);
    } else if (e.target.value === '') {
      setStartingNumber(1);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Finalize Your Mockup</h2>
        <p className="text-gray-600">Configure the final settings for your mockup generation.</p>
      </div>

      {/* Settings Card */}
      <Card>
        <CardHeader>
          <CardTitle>Mockup Settings</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-6">
            {/* Mockup Name Input */}
            <div className="space-y-2">
              <label htmlFor="mockup-name" className="block text-sm font-medium text-gray-700">
                Mockup Name
              </label>
              <Input
                id="mockup-name"
                type="text"
                value={mockupName}
                onChange={handleNameChange}
                placeholder="Enter mockup name"
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                This name will be used for your generated mockup files
              </p>
            </div>

            {/* Starting Number Input */}
            <div className="space-y-2">
              <label htmlFor="starting-number" className="block text-sm font-medium text-gray-700">
                Starting Number
              </label>
              <Input
                id="starting-number"
                type="number"
                value={startingNumber}
                onChange={handleNumberChange}
                placeholder="1"
                min="1"
                className="w-full"
              />
              <p className="text-xs text-gray-500">
                The number to start with for sequential mockup naming (e.g., MyMockup_001.png)
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Preview Card */}
      <Card>
        <CardHeader>
          <CardTitle>File Naming Preview</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="bg-gray-50 rounded-lg p-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Generated File Names:</h4>
              <div className="space-y-1 text-sm text-gray-600">
                <div className="font-mono bg-white px-2 py-1 rounded border">
                  {mockupName || 'MyMockup'}_{String(startingNumber).padStart(3, '0')}.png
                </div>
                <div className="font-mono bg-white px-2 py-1 rounded border">
                  {mockupName || 'MyMockup'}_{String(startingNumber + 1).padStart(3, '0')}.png
                </div>
                <div className="font-mono bg-white px-2 py-1 rounded border">
                  {mockupName || 'MyMockup'}_{String(startingNumber + 2).padStart(3, '0')}.png
                </div>
                {startingNumber + 2 < 100 && (
                  <div className="text-xs text-gray-400 italic">
                    ... and so on
                  </div>
                )}
              </div>
            </div>

            <div className="text-sm text-gray-600">
              <div className="flex items-start space-x-2">
                <svg
                  className="w-4 h-4 text-blue-600 mt-0.5 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <div>
                  <p className="font-medium text-gray-900">Naming Convention</p>
                  <p className="mt-1">
                    Files are automatically numbered with zero-padding (001, 002, etc.)
                    for consistent sorting and organization.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Actions Card */}
      <Card>
        <CardHeader>
          <CardTitle>Ready to Generate</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center space-x-3">
                <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                  <svg
                    className="w-5 h-5 text-green-600"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M5 13l4 4L19 7"
                    />
                  </svg>
                </div>
                <div>
                  <p className="font-medium text-green-900">Configuration Complete</p>
                  <p className="text-sm text-green-700">Your mockup is ready to be generated</p>
                </div>
              </div>
            </div>

            <div className="flex justify-end space-x-3">
              <Button variant="secondary">
                Preview Settings
              </Button>
              <Button className="flex items-center space-x-2">
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
                    d="M13 10V3L4 14h7v7l9-11h-7z"
                  />
                </svg>
                <span>Generate Mockup</span>
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}