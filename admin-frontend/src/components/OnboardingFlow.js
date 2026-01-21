import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';

const OnboardingFlow = ({ onComplete }) => {
  // const { user } = useAuth();
  const [currentStep, setCurrentStep] = useState(1);
  const [hasEtsyConnection] = useState(false);
  const [hasTemplates] = useState(false);
  const [hasMockups] = useState(false);

  const steps = [
    {
      id: 1,
      title: 'Welcome!',
      description: "Let's get you set up to create amazing Etsy listings",
      icon: '👋',
      content: (
        <div className="text-center space-y-4">
          <div className="text-6xl mb-4">🎉</div>
          <h3 className="text-xl font-semibold text-gray-900">Welcome to CraftFlow!</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            This quick setup will help you connect your Etsy shop and start creating professional mockups for your
            designs.
          </p>
          <div className="bg-blue-50 p-4 rounded-lg">
            <p className="text-sm text-blue-700">
              <strong>What you'll learn:</strong> How to connect Etsy, create templates, and generate mockups
              automatically
            </p>
          </div>
        </div>
      ),
    },
    {
      id: 2,
      title: 'Connect Your Etsy Shop',
      description: 'Link your Etsy account to start syncing orders and listings',
      icon: '🛍️',
      content: (
        <div className="text-center space-y-4">
          <div className="text-6xl mb-4">🛍️</div>
          <h3 className="text-xl font-semibold text-gray-900">Connect Your Etsy Shop</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Connect your Etsy shop to automatically sync orders, manage listings, and track your sales analytics.
          </p>
          {hasEtsyConnection ? (
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-green-700 font-medium">Etsy shop connected!</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <Link
                to="/connect-etsy"
                className="inline-block bg-orange-500 text-white px-6 py-3 rounded-lg hover:bg-orange-600 transition-colors font-medium"
              >
                Connect Etsy Shop
              </Link>
              <p className="text-xs text-gray-500">You'll be redirected to Etsy to authorize the connection</p>
            </div>
          )}
        </div>
      ),
    },
    {
      id: 3,
      title: 'Set Up Templates',
      description: 'Create listing templates for your products',
      icon: '📋',
      content: (
        <div className="text-center space-y-4">
          <div className="text-6xl mb-4">📋</div>
          <h3 className="text-xl font-semibold text-gray-900">Create Your First Template</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Templates help you quickly create consistent Etsy listings. Set up titles, descriptions, prices, and more.
          </p>
          {hasTemplates ? (
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-green-700 font-medium">Templates created!</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <Link
                to="/account"
                className="inline-block bg-blue-500 text-white px-6 py-3 rounded-lg hover:bg-blue-600 transition-colors font-medium"
              >
                Create Templates
              </Link>
              <p className="text-xs text-gray-500">Go to Account → Templates to set up your first template</p>
            </div>
          )}
        </div>
      ),
    },
    {
      id: 4,
      title: 'Create Your First Mockup',
      description: 'Generate professional product mockups',
      icon: '🎨',
      content: (
        <div className="text-center space-y-4">
          <div className="text-6xl mb-4">🎨</div>
          <h3 className="text-xl font-semibold text-gray-900">Create Your First Mockup</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Upload your designs and create professional mockups that showcase your products beautifully.
          </p>
          {hasMockups ? (
            <div className="bg-green-50 p-4 rounded-lg">
              <div className="flex items-center justify-center space-x-2">
                <svg className="w-5 h-5 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                <span className="text-green-700 font-medium">Mockups created!</span>
              </div>
            </div>
          ) : (
            <div className="space-y-3">
              <Link
                to="/mockup-creator"
                className="inline-block bg-purple-500 text-white px-6 py-3 rounded-lg hover:bg-purple-600 transition-colors font-medium"
              >
                Create Mockups
              </Link>
              <p className="text-xs text-gray-500">Upload your designs and create professional mockups</p>
            </div>
          )}
        </div>
      ),
    },
    {
      id: 5,
      title: "You're All Set!",
      description: 'Start managing your Etsy business',
      icon: '🚀',
      content: (
        <div className="text-center space-y-4">
          <div className="text-6xl mb-4">🚀</div>
          <h3 className="text-xl font-semibold text-gray-900">You're Ready to Go!</h3>
          <p className="text-gray-600 max-w-md mx-auto">
            Your setup is complete! You can now create designs, generate mockups, and manage your Etsy listings all in
            one place.
          </p>
          <div className="bg-gradient-to-r from-blue-50 to-purple-50 p-4 rounded-lg">
            <h4 className="font-semibold text-gray-900 mb-2">Quick Tips:</h4>
            <ul className="text-sm text-gray-600 space-y-1 text-left max-w-sm mx-auto">
              <li>• Use the Analytics tab to track your sales</li>
              <li>• Check Orders tab for new purchases</li>
              <li>• Upload products in the Products tab</li>
              <li>• Use Tools for batch operations</li>
            </ul>
          </div>
          <button
            onClick={() => {
              localStorage.setItem('onboarding_completed', 'true');
              onComplete && onComplete();
            }}
            className="bg-green-500 text-white px-6 py-3 rounded-lg hover:bg-green-600 transition-colors font-medium"
          >
            Start Using the Dashboard
          </button>
        </div>
      ),
    },
  ];

  const nextStep = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const skipOnboarding = () => {
    localStorage.setItem('onboarding_completed', 'true');
    onComplete && onComplete();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="p-6 border-b border-gray-200">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Getting Started</h2>
            <button onClick={skipOnboarding} className="text-gray-400 hover:text-gray-600 text-sm">
              Skip tour
            </button>
          </div>

          {/* Progress */}
          <div className="mt-4">
            <div className="flex justify-between text-sm text-gray-600 mb-2">
              <span>
                Step {currentStep} of {steps.length}
              </span>
              <span>{Math.round((currentStep / steps.length) * 100)}% complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${(currentStep / steps.length) * 100}%` }}
              />
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="p-8">{steps[currentStep - 1]?.content}</div>

        {/* Footer */}
        <div className="p-6 border-t border-gray-200 flex justify-between items-center">
          <button
            onClick={prevStep}
            disabled={currentStep === 1}
            className={`px-4 py-2 rounded-lg font-medium transition-colors ${
              currentStep === 1
                ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
            }`}
          >
            Previous
          </button>

          <div className="flex space-x-3">
            <button onClick={skipOnboarding} className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors">
              Skip for now
            </button>

            {currentStep < steps.length ? (
              <button
                onClick={nextStep}
                className="px-6 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors font-medium"
              >
                Continue
              </button>
            ) : (
              <button
                onClick={() => {
                  localStorage.setItem('onboarding_completed', 'true');
                  onComplete && onComplete();
                }}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors font-medium"
              >
                Get Started
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OnboardingFlow;
