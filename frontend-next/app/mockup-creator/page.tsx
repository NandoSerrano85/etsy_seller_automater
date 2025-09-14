'use client';

import { useState } from 'react';

interface Template {
  id: string;
  name: string;
  preview: string;
}

export default function MockupCreatorPage() {
  const [selectedTemplate, setSelectedTemplate] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string>('');

  const templates: Template[] = [
    { id: '1', name: 'T-Shirt Mockup', preview: '/placeholder-tshirt.jpg' },
    { id: '2', name: 'Mug Mockup', preview: '/placeholder-mug.jpg' },
    { id: '3', name: 'Poster Mockup', preview: '/placeholder-poster.jpg' },
    { id: '4', name: 'Phone Case Mockup', preview: '/placeholder-phone.jpg' },
  ];

  const handleGenerateMockup = async () => {
    if (!selectedTemplate) {
      setMessage('Please select a template first');
      return;
    }

    setLoading(true);
    setMessage('');

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/mockups`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            templateId: selectedTemplate,
            designData: {
              text: 'Sample Design',
              backgroundColor: '#ffffff',
              textColor: '#000000',
            },
            dimensions: {
              width: 1200,
              height: 800,
            },
          }),
        }
      );

      if (response.ok) {
        const result = await response.json();
        setMessage(
          `Mockup generated successfully! ID: ${result.mockupId || 'N/A'}`
        );
      } else {
        setMessage('Failed to generate mockup. Please try again.');
      }
    } catch (error) {
      console.error('Error generating mockup:', error);
      setMessage('Error generating mockup. Please check your connection.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Mockup Creator</h1>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Template Picker */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Choose Template</h2>
          <div className="grid grid-cols-2 gap-4">
            {templates.map((template) => (
              <div
                key={template.id}
                onClick={() => setSelectedTemplate(template.id)}
                className={`cursor-pointer border-2 rounded-lg p-4 transition-colors ${
                  selectedTemplate === template.id
                    ? 'border-primary bg-blue-50'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                <div className="bg-gray-200 h-32 rounded mb-2 flex items-center justify-center">
                  <span className="text-gray-500 text-sm">Preview</span>
                </div>
                <h3 className="font-medium text-center">{template.name}</h3>
              </div>
            ))}
          </div>
        </div>

        {/* Canvas Workspace */}
        <div>
          <h2 className="text-xl font-semibold mb-4">Design Workspace</h2>
          <div className="bg-gray-100 border-2 border-dashed border-gray-300 rounded-lg h-96 flex items-center justify-center">
            <div className="text-center text-gray-500">
              <p className="text-lg mb-2">Canvas Workspace</p>
              <p className="text-sm">Design tools will appear here</p>
            </div>
          </div>
        </div>
      </div>

      {/* Generate Button and Messages */}
      <div className="mt-8">
        <button
          onClick={handleGenerateMockup}
          disabled={loading || !selectedTemplate}
          className="bg-primary text-white px-6 py-3 rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50"
        >
          {loading ? 'Generating...' : 'Generate Mockup'}
        </button>

        {message && (
          <div
            className={`mt-4 p-4 rounded-md ${
              message.includes('successfully')
                ? 'bg-green-50 text-green-700 border border-green-200'
                : 'bg-red-50 text-red-700 border border-red-200'
            }`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
