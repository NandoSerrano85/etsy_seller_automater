'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';

interface Step3MasksProps {
  canvasRef: React.RefObject<HTMLCanvasElement>;
}

export function Step3Masks({ canvasRef }: Step3MasksProps) {
  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Create Masks</h2>
        <p className="text-gray-600">Draw masks to define areas where your designs will be applied.</p>
      </div>

      {/* Canvas Section */}
      <Card>
        <CardHeader>
          <CardTitle>Mask Canvas</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Canvas Container */}
            <div className="flex justify-center">
              <div className="w-full max-w-4xl">
                <canvas
                  ref={canvasRef}
                  className="w-full max-h-96 border border-gray-300 rounded-lg bg-white shadow-sm hover:border-gray-400 transition-colors"
                  width={800}
                  height={400}
                  style={{
                    maxHeight: '24rem', // 384px - consistent with max-h-96
                    aspectRatio: '2/1'
                  }}
                >
                  Your browser does not support the HTML5 canvas element.
                </canvas>
              </div>
            </div>

            {/* Canvas Instructions */}
            <div className="text-center text-sm text-gray-500 space-y-1">
              <p>Click and drag to draw mask areas</p>
              <p>The canvas will be populated with mask drawing tools</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mask Tools */}
      <Card>
        <CardHeader>
          <CardTitle>Mask Tools</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {/* Tool Buttons */}
            <div className="flex flex-wrap gap-3">
              <Button variant="secondary" className="flex items-center space-x-2">
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
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
                <span>Draw</span>
              </Button>

              <Button variant="secondary" className="flex items-center space-x-2">
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
                <span>Erase</span>
              </Button>

              <Button variant="secondary" className="flex items-center space-x-2">
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
                    d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                  />
                </svg>
                <span>Clear</span>
              </Button>

              <Button variant="secondary" className="flex items-center space-x-2">
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
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                <span>Copy</span>
              </Button>
            </div>

            {/* Tool Settings */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Brush Size</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="1"
                    max="50"
                    defaultValue="10"
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 min-w-[2rem]">10px</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Opacity</label>
                <div className="flex items-center space-x-2">
                  <input
                    type="range"
                    min="0"
                    max="100"
                    defaultValue="100"
                    className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                  />
                  <span className="text-sm text-gray-600 min-w-[3rem]">100%</span>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-sm font-medium text-gray-700">Tool Mode</label>
                <select className="w-full px-3 py-2 text-sm border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:border-primary">
                  <option value="draw">Draw</option>
                  <option value="erase">Erase</option>
                  <option value="select">Select</option>
                </select>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Mask Info */}
      <Card>
        <CardHeader>
          <CardTitle>Mask Information</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-sm text-gray-600 space-y-2">
            <div className="flex justify-between">
              <span>Canvas Size:</span>
              <span className="font-medium">800 × 400 pixels</span>
            </div>
            <div className="flex justify-between">
              <span>Mask Count:</span>
              <span className="font-medium">0</span>
            </div>
            <div className="flex justify-between">
              <span>Active Tool:</span>
              <span className="font-medium">Draw</span>
            </div>
          </div>

          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <div className="flex items-start space-x-2">
              <svg
                className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0"
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
              <div className="text-sm">
                <p className="text-blue-800 font-medium">Mask Drawing Tips</p>
                <p className="text-blue-700 mt-1">
                  Draw areas where you want your designs to appear. Use different tools to create precise masks for your mockups.
                </p>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}