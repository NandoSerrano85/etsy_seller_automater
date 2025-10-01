import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { BuildingStorefrontIcon, ShoppingBagIcon, ArrowRightIcon } from '@heroicons/react/24/outline';

const TemplateCreator = () => {
  const navigate = useNavigate();
  const [selectedPlatform, setSelectedPlatform] = useState(null);

  const platforms = [
    {
      id: 'etsy',
      name: 'Etsy',
      description: 'Create templates for Etsy product listings',
      icon: BuildingStorefrontIcon,
      color: 'orange',
      route: '/etsy/templates/create',
    },
    {
      id: 'shopify',
      name: 'Shopify',
      description: 'Create templates for Shopify product listings',
      icon: ShoppingBagIcon,
      color: 'green',
      route: '/shopify/templates/create',
    },
  ];

  const handlePlatformSelect = platform => {
    setSelectedPlatform(platform.id);
    setTimeout(() => {
      navigate(platform.route);
    }, 200);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Create Product Template</h1>
          <p className="text-lg text-gray-600">Choose a platform to create a reusable product template</p>
        </div>

        {/* Platform Selection */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {platforms.map(platform => (
            <button
              key={platform.id}
              onClick={() => handlePlatformSelect(platform)}
              className={`relative p-8 bg-white rounded-xl shadow-lg border-2 transition-all duration-200 ${
                selectedPlatform === platform.id
                  ? 'border-sage-500 shadow-xl transform scale-105'
                  : 'border-gray-200 hover:border-sage-300 hover:shadow-xl'
              }`}
            >
              <div className="flex flex-col items-center text-center">
                <div
                  className={`w-20 h-20 rounded-full flex items-center justify-center mb-4 ${
                    platform.color === 'orange'
                      ? 'bg-orange-100'
                      : platform.color === 'green'
                        ? 'bg-green-100'
                        : 'bg-blue-100'
                  }`}
                >
                  <platform.icon
                    className={`w-10 h-10 ${
                      platform.color === 'orange'
                        ? 'text-orange-600'
                        : platform.color === 'green'
                          ? 'text-green-600'
                          : 'text-blue-600'
                    }`}
                  />
                </div>
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{platform.name}</h3>
                <p className="text-gray-600 mb-4">{platform.description}</p>
                <div className="flex items-center text-sage-600 font-medium">
                  <span>Get Started</span>
                  <ArrowRightIcon className="w-5 h-5 ml-2" />
                </div>
              </div>
            </button>
          ))}
        </div>

        {/* Info Section */}
        <div className="mt-12 bg-white rounded-lg shadow-md p-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">What are Product Templates?</h3>
          <ul className="space-y-3 text-gray-700">
            <li className="flex items-start">
              <span className="text-sage-600 font-bold mr-2">•</span>
              <span>Save time by creating reusable product configurations</span>
            </li>
            <li className="flex items-start">
              <span className="text-sage-600 font-bold mr-2">•</span>
              <span>Maintain consistent pricing, descriptions, and settings across products</span>
            </li>
            <li className="flex items-start">
              <span className="text-sage-600 font-bold mr-2">•</span>
              <span>Quickly create new products by applying your saved templates</span>
            </li>
            <li className="flex items-start">
              <span className="text-sage-600 font-bold mr-2">•</span>
              <span>Update template settings to apply changes to future products</span>
            </li>
          </ul>
        </div>
      </div>
    </div>
  );
};

export default TemplateCreator;
