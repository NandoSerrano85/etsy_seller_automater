import React, { useState, useRef, useEffect } from 'react';

const Dropdown = ({ 
  label, 
  options, 
  value, 
  onChange, 
  className = "",
  buttonClassName = "",
  menuClassName = "",
  optionClassName = ""
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleOptionClick = (optionValue) => {
    onChange(optionValue);
    setIsOpen(false);
  };

  const selectedOption = options.find(option => option.value === value);

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <div className="flex items-center space-x-2">
        <span className="text-sm text-gray-600">{label}:</span>
        <div className="relative">
          <button
            onClick={() => setIsOpen(!isOpen)}
            className={`flex items-center justify-between px-3 py-1 text-xs bg-gray-100 rounded-lg hover:bg-gray-200 transition-colors min-w-[80px] ${buttonClassName}`}
          >
            <span className="text-gray-700">{selectedOption?.label || 'Select'}</span>
            <svg
              className={`w-3 h-3 ml-1 transition-transform ${isOpen ? 'rotate-180' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 9l-7 7-7-7"
              />
            </svg>
          </button>
          
          {isOpen && (
            <div className={`absolute top-full left-0 mt-1 bg-white border border-gray-200 rounded-lg shadow-lg z-10 min-w-[80px] ${menuClassName}`}>
              {options.map((option) => (
                <button
                  key={option.value}
                  onClick={() => handleOptionClick(option.value)}
                  className={`w-full text-left px-3 py-2 text-xs hover:bg-gray-100 transition-colors first:rounded-t-lg last:rounded-b-lg ${
                    value === option.value ? 'bg-blue-50 text-blue-600' : 'text-gray-700'
                  } ${optionClassName}`}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dropdown; 