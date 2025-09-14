'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent } from '@/components/ui/Card';
import clsx from 'clsx';

interface Step1TemplateProps {
  templates: any[];
  selectedTemplate: any | null;
  setSelectedTemplate: (template: any) => void;
}

export function Step1Template({ templates, selectedTemplate, setSelectedTemplate }: Step1TemplateProps) {
  const handleTemplateClick = (template: any) => {
    setSelectedTemplate(template);
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Choose a Template</h2>
        <p className="text-gray-600">Select a mockup template to get started with your design.</p>
      </div>

      {templates.length === 0 ? (
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
                d="M9 13h6m-3-3v6m-9 1V7a2 2 0 012-2h6l2 2h6a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2z"
              />
            </svg>
            <h3 className="mt-2 text-sm font-medium text-gray-900">No templates available</h3>
            <p className="mt-1 text-sm text-gray-500">
              Templates will appear here when they are loaded.
            </p>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
          {templates.map((template) => (
            <Card
              key={template.id}
              className={clsx(
                "cursor-pointer transition-all duration-200 hover:shadow-md",
                selectedTemplate?.id === template.id
                  ? "ring-2 ring-primary ring-offset-2 shadow-lg"
                  : "hover:ring-1 hover:ring-gray-300"
              )}
              onClick={() => handleTemplateClick(template)}
            >
              <CardContent className="p-4">
                <div className="aspect-square bg-gray-100 rounded-lg mb-3 relative overflow-hidden">
                  {template.thumbnail ? (
                    <Image
                      src={template.thumbnail}
                      alt={template.name || 'Template'}
                      fill
                      className="object-cover"
                      sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, (max-width: 1280px) 25vw, 20vw"
                    />
                  ) : (
                    <div className="flex items-center justify-center h-full">
                      <svg
                        className="w-8 h-8 text-gray-400"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                    </div>
                  )}

                  {/* Selection indicator */}
                  {selectedTemplate?.id === template.id && (
                    <div className="absolute top-2 right-2">
                      <div className="w-6 h-6 bg-primary rounded-full flex items-center justify-center">
                        <svg
                          className="w-4 h-4 text-white"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M5 13l4 4L19 7"
                          />
                        </svg>
                      </div>
                    </div>
                  )}
                </div>

                <div className="space-y-1">
                  <h4 className="font-medium text-gray-900 text-sm truncate">
                    {template.name || 'Unnamed Template'}
                  </h4>
                  {template.category && (
                    <p className="text-xs text-gray-500 truncate">
                      {template.category}
                    </p>
                  )}
                  {template.tags && template.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1">
                      {template.tags.slice(0, 2).map((tag: string, index: number) => (
                        <span
                          key={index}
                          className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded"
                        >
                          {tag}
                        </span>
                      ))}
                      {template.tags.length > 2 && (
                        <span className="inline-block px-2 py-1 text-xs bg-gray-100 text-gray-600 rounded">
                          +{template.tags.length - 2}
                        </span>
                      )}
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {selectedTemplate && (
        <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-start space-x-4">
            <div className="w-16 h-16 bg-white rounded-lg border relative overflow-hidden flex-shrink-0">
              {selectedTemplate.thumbnail ? (
                <Image
                  src={selectedTemplate.thumbnail}
                  alt={selectedTemplate.name}
                  fill
                  className="object-cover"
                />
              ) : (
                <div className="flex items-center justify-center h-full">
                  <svg
                    className="w-6 h-6 text-gray-400"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                </div>
              )}
            </div>
            <div className="flex-1">
              <h4 className="font-medium text-blue-900 mb-1">Selected Template</h4>
              <p className="text-blue-800 font-medium">{selectedTemplate.name}</p>
              {selectedTemplate.category && (
                <p className="text-blue-700 text-sm">{selectedTemplate.category}</p>
              )}
              {selectedTemplate.description && (
                <p className="text-blue-600 text-sm mt-1">{selectedTemplate.description}</p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}