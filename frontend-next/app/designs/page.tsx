'use client';

import { useState } from 'react';

type Tab = 'templates' | 'canvas' | 'presets';

export default function DesignsPage() {
  const [activeTab, setActiveTab] = useState<Tab>('templates');

  const tabs = [
    { id: 'templates', label: 'Templates', key: 'templates' as Tab },
    { id: 'canvas', label: 'Canvas Config', key: 'canvas' as Tab },
    { id: 'presets', label: 'Size Presets', key: 'presets' as Tab },
  ];

  const renderTabContent = () => {
    switch (activeTab) {
      case 'templates':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Design Templates</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-gray-100 p-4 rounded-lg">
                <div className="bg-gray-300 h-32 mb-2 rounded"></div>
                <h3 className="font-medium">Template 1</h3>
              </div>
              <div className="bg-gray-100 p-4 rounded-lg">
                <div className="bg-gray-300 h-32 mb-2 rounded"></div>
                <h3 className="font-medium">Template 2</h3>
              </div>
              <div className="bg-gray-100 p-4 rounded-lg">
                <div className="bg-gray-300 h-32 mb-2 rounded"></div>
                <h3 className="font-medium">Template 3</h3>
              </div>
            </div>
          </div>
        );
      case 'canvas':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Canvas Configuration</h2>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Canvas Width
                </label>
                <input
                  type="number"
                  className="w-full p-2 border rounded"
                  placeholder="1200"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Canvas Height
                </label>
                <input
                  type="number"
                  className="w-full p-2 border rounded"
                  placeholder="800"
                />
              </div>
              <div className="mb-4">
                <label className="block text-sm font-medium mb-2">
                  Background Color
                </label>
                <input
                  type="color"
                  className="w-full p-2 border rounded h-10"
                />
              </div>
            </div>
          </div>
        );
      case 'presets':
        return (
          <div className="p-6">
            <h2 className="text-xl font-semibold mb-4">Size Presets</h2>
            <div className="overflow-x-auto">
              <table className="w-full border-collapse border border-gray-300">
                <thead>
                  <tr className="bg-gray-50">
                    <th className="border border-gray-300 px-4 py-2 text-left">
                      Name
                    </th>
                    <th className="border border-gray-300 px-4 py-2 text-left">
                      Width
                    </th>
                    <th className="border border-gray-300 px-4 py-2 text-left">
                      Height
                    </th>
                    <th className="border border-gray-300 px-4 py-2 text-left">
                      DPI
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">
                      Business Card
                    </td>
                    <td className="border border-gray-300 px-4 py-2">1050px</td>
                    <td className="border border-gray-300 px-4 py-2">600px</td>
                    <td className="border border-gray-300 px-4 py-2">300</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">Flyer</td>
                    <td className="border border-gray-300 px-4 py-2">2550px</td>
                    <td className="border border-gray-300 px-4 py-2">3300px</td>
                    <td className="border border-gray-300 px-4 py-2">300</td>
                  </tr>
                  <tr>
                    <td className="border border-gray-300 px-4 py-2">
                      Social Media Post
                    </td>
                    <td className="border border-gray-300 px-4 py-2">1080px</td>
                    <td className="border border-gray-300 px-4 py-2">1080px</td>
                    <td className="border border-gray-300 px-4 py-2">72</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        );
      default:
        return null;
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">Designs</h1>

      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.key)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="mt-4">{renderTabContent()}</div>
    </div>
  );
}
