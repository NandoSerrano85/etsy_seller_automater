import React, { useState } from 'react';

const CreatePrinterModal = ({ isOpen, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    name: '',
    printer_type: 'dtf',
    max_width_inches: '',
    max_height_inches: '',
    dpi: 300,
    is_active: true,
    notes: '',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const printerTypes = [
    { value: 'uvdtf', label: 'UVDTF', description: 'UV Direct to Film printer for specialty transfers' },
    { value: 'dtf', label: 'DTF', description: 'Direct to Film printer for garment transfers' },
    { value: 'sublimation', label: 'Sublimation', description: 'Dye-sublimation printer for transfer printing' },
    { value: 'vinyl', label: 'Vinyl', description: 'Vinyl cutting/printing for stickers and decals' },
  ];

  const dpiOptions = [300, 400, 500, 600, 720, 1200];

  const handleInputChange = e => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));

    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  const validateForm = () => {
    const newErrors = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Printer name is required';
    } else if (formData.name.trim().length < 2) {
      newErrors.name = 'Printer name must be at least 2 characters';
    }

    if (!formData.max_width_inches || formData.max_width_inches <= 0) {
      newErrors.max_width_inches = 'Valid width is required';
    }

    if (!formData.max_height_inches || formData.max_height_inches <= 0) {
      newErrors.max_height_inches = 'Valid height is required';
    }

    if (!formData.dpi || formData.dpi < 72) {
      newErrors.dpi = 'DPI must be at least 72';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async e => {
    e.preventDefault();

    if (!validateForm()) return;

    setIsSubmitting(true);
    try {
      await onSubmit({
        name: formData.name.trim(),
        printer_type: formData.printer_type,
        max_width_inches: parseFloat(formData.max_width_inches),
        max_height_inches: parseFloat(formData.max_height_inches),
        dpi: parseInt(formData.dpi),
        description: formData.notes.trim() || null, // Backend expects 'description' not 'notes'
        supported_template_ids: [], // Start with empty array, can be configured later
      });

      // Reset form
      setFormData({
        name: '',
        printer_type: 'dtf',
        max_width_inches: '',
        max_height_inches: '',
        dpi: 300,
        is_active: true,
        notes: '',
      });
      setErrors({});
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({
        name: '',
        printer_type: 'dtf',
        max_width_inches: '',
        max_height_inches: '',
        dpi: 300,
        is_active: true,
        notes: '',
      });
      setErrors({});
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex min-h-screen items-center justify-center p-4">
        {/* Backdrop */}
        <div className="fixed inset-0 bg-black bg-opacity-50 transition-opacity" onClick={handleClose} />

        {/* Modal */}
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-lg">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-sage-900">Add New Printer</h2>
              <button
                onClick={handleClose}
                disabled={isSubmitting}
                className="text-sage-400 hover:text-sage-600 transition-colors disabled:opacity-50"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-sage-700 mb-1">
                  Printer Name *
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={formData.name}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                    errors.name
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-sage-300 focus:border-sage-500'
                  }`}
                  placeholder="Enter printer name"
                  disabled={isSubmitting}
                  autoFocus
                />
                {errors.name && <p className="mt-1 text-sm text-red-600">{errors.name}</p>}
              </div>

              <div>
                <label htmlFor="printer_type" className="block text-sm font-medium text-sage-700 mb-1">
                  Printer Type *
                </label>
                <select
                  id="printer_type"
                  name="printer_type"
                  value={formData.printer_type}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 border border-sage-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors"
                  disabled={isSubmitting}
                >
                  {printerTypes.map(type => (
                    <option key={type.value} value={type.value}>
                      {type.label}
                    </option>
                  ))}
                </select>
                <p className="mt-1 text-sm text-sage-500">
                  {printerTypes.find(t => t.value === formData.printer_type)?.description}
                </p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label htmlFor="max_width_inches" className="block text-sm font-medium text-sage-700 mb-1">
                    Max Width (inches) *
                  </label>
                  <input
                    type="number"
                    id="max_width_inches"
                    name="max_width_inches"
                    value={formData.max_width_inches}
                    onChange={handleInputChange}
                    step="0.1"
                    min="0.1"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                      errors.max_width_inches
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                        : 'border-sage-300 focus:border-sage-500'
                    }`}
                    placeholder="13.0"
                    disabled={isSubmitting}
                  />
                  {errors.max_width_inches && <p className="mt-1 text-sm text-red-600">{errors.max_width_inches}</p>}
                </div>

                <div>
                  <label htmlFor="max_height_inches" className="block text-sm font-medium text-sage-700 mb-1">
                    Max Height (inches) *
                  </label>
                  <input
                    type="number"
                    id="max_height_inches"
                    name="max_height_inches"
                    value={formData.max_height_inches}
                    onChange={handleInputChange}
                    step="0.1"
                    min="0.1"
                    className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                      errors.max_height_inches
                        ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                        : 'border-sage-300 focus:border-sage-500'
                    }`}
                    placeholder="19.0"
                    disabled={isSubmitting}
                  />
                  {errors.max_height_inches && <p className="mt-1 text-sm text-red-600">{errors.max_height_inches}</p>}
                </div>
              </div>

              <div>
                <label htmlFor="dpi" className="block text-sm font-medium text-sage-700 mb-1">
                  Resolution (DPI) *
                </label>
                <select
                  id="dpi"
                  name="dpi"
                  value={formData.dpi}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                    errors.dpi
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-sage-300 focus:border-sage-500'
                  }`}
                  disabled={isSubmitting}
                >
                  {dpiOptions.map(dpi => (
                    <option key={dpi} value={dpi}>
                      {dpi} DPI{' '}
                      {dpi >= 600 ? '(Excellent)' : dpi >= 400 ? '(Good)' : dpi >= 300 ? '(Standard)' : '(Low)'}
                    </option>
                  ))}
                </select>
                {errors.dpi && <p className="mt-1 text-sm text-red-600">{errors.dpi}</p>}
              </div>

              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-sage-700 mb-1">
                  Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  value={formData.notes}
                  onChange={handleInputChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-sage-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-sage-500 transition-colors resize-none"
                  placeholder="Optional notes about this printer..."
                  disabled={isSubmitting}
                />
              </div>

              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="is_active"
                  name="is_active"
                  checked={formData.is_active}
                  onChange={handleInputChange}
                  disabled={isSubmitting}
                  className="h-4 w-4 text-sage-600 focus:ring-sage-500 border-sage-300 rounded"
                />
                <label htmlFor="is_active" className="ml-2 block text-sm text-sage-700">
                  Printer is active and available for use
                </label>
              </div>

              <div className="flex justify-end space-x-3 pt-4">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isSubmitting}
                  className="px-4 py-2 text-sage-700 bg-sage-100 hover:bg-sage-200 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="px-4 py-2 bg-sage-600 hover:bg-sage-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 flex items-center"
                >
                  {isSubmitting && (
                    <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path
                        className="opacity-75"
                        fill="currentColor"
                        d="m4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                      />
                    </svg>
                  )}
                  {isSubmitting ? 'Adding...' : 'Add Printer'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CreatePrinterModal;
