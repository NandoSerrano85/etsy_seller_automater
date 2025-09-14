'use client';

import React from 'react';
import Image from 'next/image';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card';
import Button from '@/components/ui/Button';

interface Template {
  id: string;
  name: string;
  thumbnail: string;
  category: string;
}

interface Step1TemplateProps {
  templates: Template[];
  selectedTemplate: Template | null;
  onTemplateSelect: (template: Template) => void;
  onLoadTemplates: () => void;
  loading: boolean;
}

export function Step1Template({
  templates,
  selectedTemplate,
  onTemplateSelect,
  onLoadTemplates,
  loading
}: Step1TemplateProps) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>Choose a Template</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex justify-between items-center mb-4">
            <p className="text-sm text-gray-600">
              Select a mockup template to get started
            </p>
            <Button
              onClick={onLoadTemplates}
              disabled={loading}
              variant="secondary"
            >
              {loading ? 'Loading...' : 'Refresh Templates'}
            </Button>
          </div>

          {templates.length === 0 ? (
            <div className="text-center py-8 bg-gray-50 rounded-lg">
              <p className="text-gray-500 mb-4">No templates available</p>
              <Button onClick={onLoadTemplates} disabled={loading}>
                {loading ? 'Loading...' : 'Load Templates'}
              </Button>
            </div>
          ) : (
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
              {templates.map((template) => (
                <div
                  key={template.id}
                  className={`cursor-pointer rounded-lg border-2 p-2 transition-colors ${
                    selectedTemplate?.id === template.id
                      ? 'border-primary bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                  onClick={() => onTemplateSelect(template)}
                >
                  <div className="aspect-square bg-gray-100 rounded mb-2 relative overflow-hidden">
                    <Image
                      src={template.thumbnail || '/placeholder-template.png'}
                      alt={template.name}
                      fill
                      className="object-cover"
                    />
                  </div>
                  <h4 className="text-sm font-medium text-gray-900 truncate">
                    {template.name}
                  </h4>
                  <p className="text-xs text-gray-500 truncate">
                    {template.category}
                  </p>
                </div>
              ))}
            </div>
          )}

          {selectedTemplate && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Selected Template</h4>
              <div className="flex items-center space-x-3">
                <div className="w-12 h-12 bg-white rounded border relative overflow-hidden">
                  <Image
                    src={selectedTemplate.thumbnail || '/placeholder-template.png'}
                    alt={selectedTemplate.name}
                    fill
                    className="object-cover"
                  />
                </div>
                <div>
                  <p className="font-medium text-blue-900">{selectedTemplate.name}</p>
                  <p className="text-sm text-blue-700">{selectedTemplate.category}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}