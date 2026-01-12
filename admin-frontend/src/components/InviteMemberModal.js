import React, { useState } from 'react';
import useOrganizationStore from '../stores/organizationStore';

const InviteMemberModal = ({ isOpen, organizationId, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    email: '',
    role: 'member',
  });
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errors, setErrors] = useState({});

  const { isOwner } = useOrganizationStore();

  const handleInputChange = e => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value,
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

    if (!formData.email.trim()) {
      newErrors.email = 'Email is required';
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
      newErrors.email = 'Please enter a valid email address';
    }

    if (!formData.role) {
      newErrors.role = 'Role is required';
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
        email: formData.email.trim(),
        role: formData.role,
      });

      // Reset form
      setFormData({ email: '', role: 'member' });
      setErrors({});
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      setFormData({ email: '', role: 'member' });
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
        <div className="relative bg-white rounded-lg shadow-xl w-full max-w-md">
          <div className="p-6">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-xl font-semibold text-sage-900">Invite Member</h2>
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
                <label htmlFor="email" className="block text-sm font-medium text-sage-700 mb-1">
                  Email Address *
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={formData.email}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                    errors.email
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-sage-300 focus:border-sage-500'
                  }`}
                  placeholder="Enter email address"
                  disabled={isSubmitting}
                  autoFocus
                />
                {errors.email && <p className="mt-1 text-sm text-red-600">{errors.email}</p>}
              </div>

              <div>
                <label htmlFor="role" className="block text-sm font-medium text-sage-700 mb-1">
                  Role *
                </label>
                <select
                  id="role"
                  name="role"
                  value={formData.role}
                  onChange={handleInputChange}
                  className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-sage-500 transition-colors ${
                    errors.role
                      ? 'border-red-300 focus:border-red-500 focus:ring-red-500'
                      : 'border-sage-300 focus:border-sage-500'
                  }`}
                  disabled={isSubmitting}
                >
                  <option value="member">Member</option>
                  <option value="admin">Admin</option>
                  {isOwner() && <option value="owner">Owner</option>}
                </select>
                {errors.role && <p className="mt-1 text-sm text-red-600">{errors.role}</p>}
              </div>

              <div className="bg-sage-50 p-4 rounded-lg">
                <h4 className="text-sm font-medium text-sage-900 mb-2">Role Permissions:</h4>
                <div className="text-xs text-sage-600 space-y-1">
                  {formData.role === 'member' && (
                    <ul className="list-disc list-inside space-y-1">
                      <li>View organization details</li>
                      <li>Access shared resources</li>
                    </ul>
                  )}
                  {formData.role === 'admin' && (
                    <ul className="list-disc list-inside space-y-1">
                      <li>All member permissions</li>
                      <li>Invite and manage members</li>
                      <li>Edit organization settings</li>
                    </ul>
                  )}
                  {formData.role === 'owner' && (
                    <ul className="list-disc list-inside space-y-1">
                      <li>All admin permissions</li>
                      <li>Delete organization</li>
                      <li>Transfer ownership</li>
                    </ul>
                  )}
                </div>
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
                  {isSubmitting ? 'Sending...' : 'Send Invitation'}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
};

export default InviteMemberModal;
