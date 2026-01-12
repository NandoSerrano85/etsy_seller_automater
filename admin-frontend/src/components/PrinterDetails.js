import React, { useState, useEffect } from 'react';
import printerService from '../services/printerService';
import usePrinterStore from '../stores/printerStore';
import { useNotifications } from './NotificationSystem';
import EditPrinterModal from './EditPrinterModal';
import TemplateSelector from './TemplateSelector';

const PrinterDetails = ({ printer, isDefault, onPrinterUpdate }) => {
  const [templates, setTemplates] = useState([]);
  const [templatesLoading, setTemplatesLoading] = useState(false);
  const [showEditModal, setShowEditModal] = useState(false);
  const [showTemplateSelector, setShowTemplateSelector] = useState(false);
  const [settingDefault, setSettingDefault] = useState(false);

  const { addNotification } = useNotifications();
  const { setDefaultPrinter, updatePrinter, removePrinter } = usePrinterStore();

  useEffect(() => {
    if (printer?.id) {
      loadPrinterTemplates();
    }
  }, [printer?.id]);

  const loadPrinterTemplates = async () => {
    if (!printer?.id) return;

    setTemplatesLoading(true);
    try {
      const result = await printerService.getPrinterTemplates(printer.id);
      if (result.success) {
        setTemplates(result.data);
      } else {
        addNotification({
          type: 'error',
          message: `Failed to load templates: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to load printer templates',
      });
    } finally {
      setTemplatesLoading(false);
    }
  };

  const handleSetDefault = async () => {
    setSettingDefault(true);
    try {
      const result = await printerService.setDefaultPrinter(printer.id);
      if (result.success) {
        setDefaultPrinter(printer);
        addNotification({
          type: 'success',
          message: `${printer.name} is now your default printer`,
        });
        onPrinterUpdate();
      } else {
        addNotification({
          type: 'error',
          message: `Failed to set default printer: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to set default printer',
      });
    } finally {
      setSettingDefault(false);
    }
  };

  const handleDeletePrinter = async () => {
    if (!window.confirm(`Are you sure you want to delete "${printer.name}"? This action cannot be undone.`)) {
      return;
    }

    try {
      const result = await printerService.deletePrinter(printer.id);
      if (result.success) {
        removePrinter(printer.id);
        addNotification({
          type: 'success',
          message: 'Printer deleted successfully',
        });
        onPrinterUpdate();
      } else {
        addNotification({
          type: 'error',
          message: `Failed to delete printer: ${result.error}`,
        });
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to delete printer',
      });
    }
  };

  const getPrinterTypeIcon = printerType => {
    switch (printerType) {
      case 'inkjet':
        return '🖨️';
      case 'laser':
        return '⚡';
      case 'thermal':
        return '🔥';
      case 'sublimation':
        return '🎨';
      default:
        return '🖨️';
    }
  };

  const formatPrinterType = type => {
    return type.charAt(0).toUpperCase() + type.slice(1);
  };

  const getDpiRecommendation = dpi => {
    if (dpi >= 600) return { text: 'Excellent', color: 'text-green-600' };
    if (dpi >= 400) return { text: 'Good', color: 'text-blue-600' };
    if (dpi >= 300) return { text: 'Standard', color: 'text-yellow-600' };
    return { text: 'Low', color: 'text-red-600' };
  };

  const dpiRec = getDpiRecommendation(printer.dpi);

  return (
    <div className="space-y-6">
      {/* Printer Header */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200">
        <div className="p-6 border-b border-sage-200">
          <div className="flex justify-between items-start">
            <div className="flex items-start space-x-4">
              <div className="text-3xl">{getPrinterTypeIcon(printer.printer_type)}</div>
              <div className="flex-1">
                <div className="flex items-center space-x-3 mb-2">
                  <h2 className="text-2xl font-semibold text-sage-900">{printer.name}</h2>
                  {isDefault && (
                    <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800 border border-blue-200">
                      Default Printer
                    </span>
                  )}
                  <span
                    className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${
                      printer.is_active
                        ? 'bg-green-100 text-green-800 border border-green-200'
                        : 'bg-yellow-100 text-yellow-800 border border-yellow-200'
                    }`}
                  >
                    {printer.is_active ? 'Active' : 'Inactive'}
                  </span>
                </div>
                <p className="text-sage-600 text-lg">{formatPrinterType(printer.printer_type)} Printer</p>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              {!isDefault && (
                <button
                  onClick={handleSetDefault}
                  disabled={settingDefault}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center space-x-2"
                >
                  {settingDefault && (
                    <svg className="animate-spin h-4 w-4" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  )}
                  <span>{settingDefault ? 'Setting...' : 'Set Default'}</span>
                </button>
              )}

              <button
                onClick={() => setShowEditModal(true)}
                className="p-2 text-sage-600 hover:text-sage-800 hover:bg-sage-50 rounded-lg transition-colors"
                title="Edit printer"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                  />
                </svg>
              </button>

              <button
                onClick={handleDeletePrinter}
                className="p-2 text-red-600 hover:text-red-800 hover:bg-red-50 rounded-lg transition-colors"
                title="Delete printer"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
                  />
                </svg>
              </button>
            </div>
          </div>
        </div>

        {/* Printer Specifications */}
        <div className="p-6">
          <h3 className="text-lg font-semibold text-sage-900 mb-4">Specifications</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
            <div>
              <div className="text-sm text-sage-500 mb-1">Print Area</div>
              <div className="text-lg font-medium text-sage-900">
                {printer.max_width_inches}" × {printer.max_height_inches}"
              </div>
            </div>

            <div>
              <div className="text-sm text-sage-500 mb-1">Resolution</div>
              <div className="flex items-center space-x-2">
                <span className="text-lg font-medium text-sage-900">{printer.dpi} DPI</span>
                <span className={`text-sm font-medium ${dpiRec.color}`}>({dpiRec.text})</span>
              </div>
            </div>

            <div>
              <div className="text-sm text-sage-500 mb-1">Printer Type</div>
              <div className="text-lg font-medium text-sage-900">{formatPrinterType(printer.printer_type)}</div>
            </div>

            <div>
              <div className="text-sm text-sage-500 mb-1">Status</div>
              <div className={`text-lg font-medium ${printer.is_active ? 'text-green-600' : 'text-yellow-600'}`}>
                {printer.is_active ? 'Active' : 'Inactive'}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Supported Templates */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200">
        <div className="p-6 border-b border-sage-200">
          <div className="flex justify-between items-center">
            <h3 className="text-xl font-semibold text-sage-900">Supported Templates</h3>
            <button
              onClick={() => setShowTemplateSelector(true)}
              className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              <span>Manage Templates</span>
            </button>
          </div>
        </div>

        <div className="p-6">
          {templatesLoading ? (
            <div className="animate-pulse space-y-3">
              {[1, 2, 3].map(i => (
                <div key={i} className="h-16 bg-sage-100 rounded-lg"></div>
              ))}
            </div>
          ) : templates.length === 0 ? (
            <div className="text-center py-8">
              <div className="text-sage-400 mb-4">
                <svg className="w-12 h-12 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={1}
                    d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <h4 className="text-lg font-medium text-sage-900 mb-2">No Templates</h4>
              <p className="text-sage-600 mb-4">This printer doesn't have any supported templates configured yet.</p>
              <button
                onClick={() => setShowTemplateSelector(true)}
                className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors"
              >
                Add Templates
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {templates.map(template => (
                <div
                  key={template.id}
                  className="border border-sage-200 rounded-lg p-4 hover:border-sage-300 transition-colors"
                >
                  <div className="flex items-center space-x-3">
                    <div className="w-12 h-12 bg-sage-100 rounded-lg flex items-center justify-center flex-shrink-0">
                      <svg className="w-6 h-6 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <h4 className="font-medium text-sage-900 truncate">{template.name}</h4>
                      {template.template_title && (
                        <p className="text-sm text-sage-500 truncate">{template.template_title}</p>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Edit Printer Modal */}
      {showEditModal && (
        <EditPrinterModal
          isOpen={showEditModal}
          printer={printer}
          onClose={() => setShowEditModal(false)}
          onSubmit={() => {
            setShowEditModal(false);
            onPrinterUpdate();
          }}
        />
      )}

      {/* Template Selector Modal */}
      {showTemplateSelector && (
        <TemplateSelector
          printerId={printer.id}
          currentTemplateIds={printer.supported_template_ids || []}
          onTemplatesUpdated={() => {
            loadPrinterTemplates();
            onPrinterUpdate();
          }}
          onClose={() => setShowTemplateSelector(false)}
        />
      )}
    </div>
  );
};

export default PrinterDetails;
