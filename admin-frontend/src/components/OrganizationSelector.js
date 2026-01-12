import React, { useState, useRef, useEffect } from 'react';
import useOrganizationStore from '../stores/organizationStore';

const OrganizationSelector = ({ onOrganizationChange, selectedOrgId, className = '' }) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  const { organizations, currentOrganization, setCurrentOrganization } = useOrganizationStore();

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = event => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, []);

  const handleOrganizationSelect = org => {
    setCurrentOrganization(org);
    onOrganizationChange?.(org.id);
    setIsOpen(false);
  };

  const selectedOrg = selectedOrgId ? organizations.find(org => org.id === selectedOrgId) : currentOrganization;

  if (organizations.length === 0) {
    return null;
  }

  return (
    <div className={`relative ${className}`} ref={dropdownRef}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center space-x-2 bg-white border border-sage-300 rounded-lg px-4 py-2 text-sm font-medium text-sage-700 hover:bg-sage-50 focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors min-w-48"
      >
        <div className="flex items-center space-x-2 flex-1">
          <div className="h-6 w-6 bg-sage-300 rounded-full flex items-center justify-center">
            <span className="text-sage-700 font-medium text-xs">
              {selectedOrg?.name?.charAt(0)?.toUpperCase() || '?'}
            </span>
          </div>
          <span className="truncate">{selectedOrg?.name || 'Select Organization'}</span>
        </div>

        <svg
          className={`w-4 h-4 transition-transform ${isOpen ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isOpen && (
        <div className="absolute z-50 mt-2 w-full bg-white border border-sage-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
          <div className="p-2">
            {organizations.map(org => (
              <button
                key={org.id}
                onClick={() => handleOrganizationSelect(org)}
                className={`w-full flex items-center space-x-3 px-3 py-2 rounded-md text-sm transition-colors ${
                  selectedOrg?.id === org.id ? 'bg-sage-100 text-sage-900' : 'text-sage-700 hover:bg-sage-50'
                }`}
              >
                <div className="h-6 w-6 bg-sage-300 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-sage-700 font-medium text-xs">{org.name.charAt(0).toUpperCase()}</span>
                </div>

                <div className="flex-1 text-left min-w-0">
                  <div className="font-medium truncate">{org.name}</div>
                  <div className="text-xs text-sage-500 capitalize">{org.user_role}</div>
                </div>

                {selectedOrg?.id === org.id && (
                  <svg className="w-4 h-4 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                )}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default OrganizationSelector;
