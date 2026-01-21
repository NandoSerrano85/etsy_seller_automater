import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import usePrinterStore from '../stores/printerStore';
import useAuthStore from '../stores/authStore';
import printerService from '../services/printerService';
import { useNotifications } from '../components/NotificationSystem';
import PrinterList from '../components/PrinterList';
import PrinterDetails from '../components/PrinterDetails';
import CreatePrinterModal from '../components/CreatePrinterModal';

const PrinterManagement = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedPrinterId, setSelectedPrinterId] = useState(searchParams.get('printer') || null);

  const { addNotification } = useNotifications();
  const { isUserAuthenticated } = useAuthStore();
  const {
    printers,
    defaultPrinter,
    printersLoading,
    printersError,
    setPrinters,
    setDefaultPrinter,
    setPrintersLoading,
    setPrintersError,
    addPrinter,
  } = usePrinterStore();

  // Load printers on mount
  useEffect(() => {
    if (isUserAuthenticated) {
      loadPrinters();
    }
  }, [isUserAuthenticated]);

  // Update URL when printer is selected
  useEffect(() => {
    if (selectedPrinterId) {
      setSearchParams({ printer: selectedPrinterId });
    } else {
      setSearchParams({});
    }
  }, [selectedPrinterId, setSearchParams]);

  const loadPrinters = async () => {
    setPrintersLoading(true);
    setPrintersError(null);

    try {
      const result = await printerService.getUserPrinters();
      if (result.success) {
        setPrinters(result.data);

        // Set default printer if available
        const defaultPrinter = result.data.find(p => p.is_default);
        if (defaultPrinter) {
          setDefaultPrinter(defaultPrinter);
        }
      } else {
        setPrintersError(result.error);
        addNotification({
          type: 'error',
          message: `Failed to load printers: ${result.error}`,
        });
      }
    } catch (error) {
      setPrintersError('Failed to load printers');
      addNotification({
        type: 'error',
        message: 'Failed to load printers',
      });
    } finally {
      setPrintersLoading(false);
    }
  };

  const handleCreatePrinter = async printerData => {
    try {
      const result = await printerService.createPrinter(printerData);
      if (result.success) {
        addPrinter(result.data);
        setShowCreateModal(false);
        addNotification({
          type: 'success',
          message: 'Printer created successfully!',
        });

        // If this is the first printer, select it
        if (printers.length === 0) {
          setSelectedPrinterId(result.data.id);
        }
      } else {
        addNotification({
          type: 'error',
          message: `Failed to create printer: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to create printer',
      });
    }
  };

  const handlePrinterSelect = printerId => {
    setSelectedPrinterId(printerId);
  };

  const selectedPrinter = selectedPrinterId ? printers.find(printer => printer.id === selectedPrinterId) : null;

  if (printersLoading && printers.length === 0) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
          <p className="text-sage-600">Loading printers...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-sage-50 via-mint-25 to-lavender-50">
      <div className="container mx-auto px-4 py-8">
        <div className="flex justify-between items-center mb-8">
          <div>
            <h1 className="text-3xl font-bold text-sage-900">Printer Management</h1>
            <p className="text-sage-600 mt-2">Manage your printers and printing capabilities</p>
          </div>

          <button
            onClick={() => setShowCreateModal(true)}
            className="bg-sage-600 hover:bg-sage-700 text-white px-6 py-2 rounded-lg font-medium transition-colors flex items-center space-x-2"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            <span>Add Printer</span>
          </button>
        </div>

        {printersError && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Error:</p>
            <p>{printersError}</p>
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Printer List */}
          <div className="lg:col-span-1">
            <PrinterList
              printers={printers}
              selectedPrinterId={selectedPrinterId}
              defaultPrinterId={defaultPrinter?.id}
              onPrinterSelect={handlePrinterSelect}
              onRefresh={loadPrinters}
            />
          </div>

          {/* Printer Details */}
          <div className="lg:col-span-2">
            {selectedPrinter ? (
              <PrinterDetails
                printer={selectedPrinter}
                isDefault={selectedPrinter.id === defaultPrinter?.id}
                onPrinterUpdate={loadPrinters}
              />
            ) : (
              <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-8 text-center">
                <div className="text-sage-400 mb-4">
                  <svg className="w-16 h-16 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={1}
                      d="M17 17h2a2 2 0 002-2v-4a2 2 0 00-2-2H5a2 2 0 00-2 2v4a2 2 0 002 2h2m2 4h6a2 2 0 002-2v-9a2 2 0 00-2-2H9a2 2 0 00-2 2v9a2 2 0 002 2z"
                    />
                  </svg>
                </div>
                <h3 className="text-xl font-medium text-sage-900 mb-2">
                  {printers.length === 0 ? 'No Printers Added' : 'Select a Printer'}
                </h3>
                <p className="text-sage-600">
                  {printers.length === 0
                    ? 'Add your first printer to get started with automated printing.'
                    : 'Choose a printer from the list to view its details and manage settings.'}
                </p>
                {printers.length === 0 && (
                  <button
                    onClick={() => setShowCreateModal(true)}
                    className="mt-4 bg-sage-600 hover:bg-sage-700 text-white px-6 py-2 rounded-lg font-medium transition-colors"
                  >
                    Add Your First Printer
                  </button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Create Printer Modal */}
      {showCreateModal && (
        <CreatePrinterModal
          isOpen={showCreateModal}
          onClose={() => setShowCreateModal(false)}
          onSubmit={handleCreatePrinter}
        />
      )}
    </div>
  );
};

export default PrinterManagement;
