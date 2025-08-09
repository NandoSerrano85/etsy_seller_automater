import React from 'react';

const ProgressIndicator = ({ 
  steps, 
  currentStep, 
  variant = 'dots', // 'dots', 'bar', 'numbered'
  size = 'md' // 'sm', 'md', 'lg'
}) => {
  const sizeClasses = {
    sm: 'w-2 h-2',
    md: 'w-3 h-3', 
    lg: 'w-4 h-4'
  };

  if (variant === 'bar') {
    const progress = ((currentStep - 1) / (steps.length - 1)) * 100;
    
    return (
      <div className="w-full bg-gray-200 rounded-full h-2 mb-4">
        <div 
          className="bg-blue-500 h-2 rounded-full transition-all duration-300 ease-in-out"
          style={{ width: `${progress}%` }}
        />
        <div className="flex justify-between mt-2 text-xs text-gray-600">
          <span>Step {currentStep}</span>
          <span>{steps.length} steps total</span>
        </div>
      </div>
    );
  }

  if (variant === 'numbered') {
    return (
      <div className="flex items-center justify-center space-x-4 mb-6">
        {steps.map((step, index) => (
          <div key={index} className="flex items-center">
            <div className={`
              flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium transition-all
              ${index < currentStep - 1 
                ? 'bg-green-500 text-white' 
                : index === currentStep - 1 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-200 text-gray-600'
              }
            `}>
              {index < currentStep - 1 ? (
                <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              ) : (
                index + 1
              )}
            </div>
            {index < steps.length - 1 && (
              <div className={`w-12 h-1 mx-2 ${
                index < currentStep - 1 ? 'bg-green-500' : 'bg-gray-200'
              }`} />
            )}
          </div>
        ))}
      </div>
    );
  }

  // Default dots variant
  return (
    <div className="flex justify-center space-x-2 mb-4">
      {steps.map((_, index) => (
        <div
          key={index}
          className={`
            ${sizeClasses[size]} rounded-full transition-all duration-200
            ${index < currentStep 
              ? 'bg-blue-500' 
              : index === currentStep 
              ? 'bg-blue-300' 
              : 'bg-gray-300'
            }
          `}
        />
      ))}
    </div>
  );
};

export default ProgressIndicator;