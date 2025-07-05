import React from 'react';
import { Link } from 'react-router-dom';

const ToolsTab = () => (
  <div className="space-y-8">
    <h2 className="text-2xl font-bold text-gray-900">Tools</h2>
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div className="card p-6">
        <h3 className="text-xl font-semibold text-gray-900 mb-3">Mockup Creator</h3>
        <p className="text-gray-600 mb-4">
          Create masks for mockup images by drawing polygons or rectangles. This tool helps you define areas where designs will be placed on mockup templates.
        </p>
        <Link to="/mockup-creator" className="btn-primary">
          Open Mask Creator
        </Link>
      </div>
    </div>
  </div>
);

export default ToolsTab; 