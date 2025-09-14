import React, { useState } from 'react';
import TemplateEditor from '../components/TemplateEditor';
import TemplateGallery from '../components/TemplateGallery';
import { PlusIcon, RectangleStackIcon, ArrowLeftIcon } from '@heroicons/react/24/outline';

const TemplateManager = () => {
  const [currentView, setCurrentView] = useState('gallery'); // 'gallery' or 'editor'
  const [editingTemplate, setEditingTemplate] = useState(null);

  const handleCreateNew = () => {
    setEditingTemplate(null);
    setCurrentView('editor');
  };

  const handleEditTemplate = template => {
    setEditingTemplate(template);
    setCurrentView('editor');
  };

  const handleBackToGallery = () => {
    setEditingTemplate(null);
    setCurrentView('gallery');
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {currentView === 'gallery' ? (
        <div className="max-w-7xl mx-auto p-6">
          <TemplateGallery onCreateNew={handleCreateNew} onEditTemplate={handleEditTemplate} />
        </div>
      ) : (
        <div>
          {/* Navigation Bar */}
          <div className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-6 py-4">
              <div className="flex items-center space-x-4">
                <button onClick={handleBackToGallery} className="flex items-center text-gray-600 hover:text-gray-900">
                  <ArrowLeftIcon className="w-5 h-5 mr-2" />
                  Back to Gallery
                </button>

                <div className="h-6 w-px bg-gray-300"></div>

                <div className="flex items-center text-gray-900">
                  <RectangleStackIcon className="w-5 h-5 mr-2" />
                  {editingTemplate ? `Edit Template: ${editingTemplate.name}` : 'Create New Template'}
                </div>
              </div>
            </div>
          </div>

          {/* Template Editor */}
          <TemplateEditor
            initialTemplate={editingTemplate}
            onSave={handleBackToGallery}
            onCancel={handleBackToGallery}
          />
        </div>
      )}
    </div>
  );
};

export default TemplateManager;
