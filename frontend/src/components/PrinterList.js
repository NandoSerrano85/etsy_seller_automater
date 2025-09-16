import React from 'react';
import usePrinterStore from '../stores/printerStore';

const PrinterList = ({ printers, selectedPrinterId, defaultPrinterId, onPrinterSelect, onRefresh }) => {
  const { printersLoading } = usePrinterStore();

  const getPrinterTypeIcon = printerType => {
    switch (printerType) {
      case 'uvdtf':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z"
            />
          </svg>
        );
      case 'dtf':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z"
            />
          </svg>
        );
      case 'sublimation':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zM21 5a2 2 0 00-2-2h-4a2 2 0 00-2 2v12a4 4 0 004 4 4 4 0 004-4V5z"
            />
          </svg>
        );
      case 'vinyl':
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7 4V2a1 1 0 011-1h8a1 1 0 011 1v2m-9 0h10m-10 0a2 2 0 00-2 2v14a2 2 0 002 2h10a2 2 0 002-2V6a2 2 0 00-2-2M9 12h6m-6 4h6"
            />
          </svg>
        );
      default:
        return (
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z"
            />
          </svg>
        );
    }
  };

  const getStatusColor = isActive => {
    return isActive ? 'text-green-600' : 'text-yellow-600';
  };

  const formatPrinterType = type => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  if (printersLoading && printers.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <div className="animate-pulse">
          <div className="h-4 bg-sage-200 rounded w-3/4 mb-4"></div>
          <div className="space-y-3">
            {[1, 2, 3].map(i => (
              <div key={i} className="h-20 bg-sage-100 rounded-lg"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border border-sage-200">
      <div className="p-6 border-b border-sage-200">
        <div className="flex justify-between items-center">
          <h2 className="text-xl font-semibold text-sage-900">My Printers</h2>
          <button
            onClick={onRefresh}
            disabled={printersLoading}
            className="p-2 text-sage-500 hover:text-sage-700 hover:bg-sage-50 rounded-lg transition-colors disabled:opacity-50"
            title="Refresh printers"
          >
            <svg
              className={`w-5 h-5 ${printersLoading ? 'animate-spin' : ''}`}
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          </button>
        </div>
      </div>

      <div className="p-6">
        {printers.length === 0 ? (
          <div className="text-center py-8">
            <div className="text-sage-400 mb-4">
              <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={1}
                  d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h3 className="text-lg font-medium text-sage-900 mb-2">No Printers</h3>
            <p className="text-sage-600 mb-4">You haven't added any printers yet.</p>
          </div>
        ) : (
          <div className="space-y-3">
            {printers.map(printer => (
              <div
                key={printer.id}
                onClick={() => onPrinterSelect(printer.id)}
                className={`p-4 border rounded-lg cursor-pointer transition-all hover:shadow-md ${
                  selectedPrinterId === printer.id
                    ? 'border-sage-500 bg-sage-50 shadow-sm'
                    : 'border-sage-200 hover:border-sage-300'
                }`}
              >
                <div className="flex justify-between items-start">
                  <div className="flex items-start space-x-3 flex-1 min-w-0">
                    <div className="flex-shrink-0 p-2 bg-sage-100 rounded-lg">
                      {getPrinterTypeIcon(printer.printer_type)}
                    </div>

                    <div className="flex-1 min-w-0">
                      <div className="flex items-center space-x-2 mb-1">
                        <h3 className="text-lg font-semibold text-sage-900 truncate">{printer.name}</h3>
                        {printer.id === defaultPrinterId && (
                          <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800 border border-blue-200">
                            Default
                          </span>
                        )}
                      </div>

                      <p className="text-sm text-sage-600 mb-2">
                        {formatPrinterType(printer.printer_type)} • {printer.dpi} DPI
                      </p>

                      <div className="flex items-center text-sm text-sage-500 space-x-4">
                        <span className="flex items-center">
                          <svg className="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                            />
                          </svg>
                          {printer.max_width_inches}" × {printer.max_height_inches}"
                        </span>

                        <span className={`flex items-center ${getStatusColor(printer.is_active)}`}>
                          <div
                            className={`w-2 h-2 rounded-full mr-1 ${printer.is_active ? 'bg-green-500' : 'bg-yellow-500'}`}
                          ></div>
                          {printer.is_active ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};

export default PrinterList;
