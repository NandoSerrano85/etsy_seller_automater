import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import {
  GlobeAltIcon,
  CheckCircleIcon,
  XCircleIcon,
  ArrowPathIcon,
  ClipboardDocumentIcon,
  ShieldCheckIcon,
  EyeIcon,
  EyeSlashIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  LinkIcon,
  LockClosedIcon,
} from '@heroicons/react/24/outline';

const CraftFlowDomainSettings = () => {
  const { userToken: token, user } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [provisioningSSL, setProvisioningSSL] = useState(false);

  // Domain settings state
  const [subdomain, setSubdomain] = useState('');
  const [customDomain, setCustomDomain] = useState('');
  const [domainStatus, setDomainStatus] = useState({
    subdomain: null,
    custom_domain: null,
    domain_verified: false,
    domain_verification_token: null,
    ssl_status: null,
    ssl_expires_at: null,
    is_published: false,
    maintenance_mode: false,
  });
  const [dnsInstructions, setDnsInstructions] = useState(null);
  const [subdomainError, setSubdomainError] = useState('');
  const [customDomainError, setCustomDomainError] = useState('');

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  // Storefront base URL - path-based routing
  const STOREFRONT_BASE_URL = process.env.REACT_APP_STOREFRONT_URL || 'https://storefront.craftflow.store';

  // Load domain status on mount
  useEffect(() => {
    loadDomainStatus();
  }, []);

  const loadDomainStatus = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/storefront/domain/status`, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.data) {
        setDomainStatus(response.data);
        setSubdomain(response.data.subdomain || '');
        setCustomDomain(response.data.custom_domain || '');
      }
    } catch (error) {
      console.error('Error loading domain status:', error);
      if (error.response?.status !== 404) {
        addNotification('error', 'Failed to load domain settings');
      }
    } finally {
      setLoading(false);
    }
  };

  // Subdomain validation
  const validateSubdomain = value => {
    if (!value) return '';
    if (value.length < 3) return 'Subdomain must be at least 3 characters';
    if (value.length > 63) return 'Subdomain must be less than 63 characters';
    if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?$/.test(value)) {
      return 'Subdomain can only contain lowercase letters, numbers, and hyphens';
    }
    return '';
  };

  // Custom domain validation
  const validateCustomDomain = value => {
    if (!value) return '';
    if (!/^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)+$/.test(value.toLowerCase())) {
      return 'Please enter a valid domain (e.g., shop.example.com)';
    }
    return '';
  };

  // Save subdomain
  const handleSaveSubdomain = async () => {
    const error = validateSubdomain(subdomain);
    if (error) {
      setSubdomainError(error);
      return;
    }

    try {
      setSaving(true);
      await axios.post(
        `${API_BASE_URL}/api/ecommerce/storefront/domain/subdomain`,
        { subdomain },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addNotification('success', 'Store URL saved successfully');
      await loadDomainStatus();
    } catch (error) {
      console.error('Error saving store URL:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to save store URL';
      addNotification('error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Remove store URL
  const handleRemoveSubdomain = async () => {
    if (!window.confirm('Are you sure you want to remove your store URL?')) return;

    try {
      setSaving(true);
      await axios.delete(`${API_BASE_URL}/api/ecommerce/storefront/domain/subdomain`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setSubdomain('');
      addNotification('success', 'Store URL removed');
      await loadDomainStatus();
    } catch (error) {
      console.error('Error removing store URL:', error);
      addNotification('error', 'Failed to remove store URL');
    } finally {
      setSaving(false);
    }
  };

  // Set custom domain
  const handleSetCustomDomain = async () => {
    const error = validateCustomDomain(customDomain);
    if (error) {
      setCustomDomainError(error);
      return;
    }

    try {
      setSaving(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/ecommerce/storefront/domain/domain`,
        { domain: customDomain },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addNotification('success', 'Custom domain configured. Please add the DNS records to verify ownership.');
      setDnsInstructions(response.data);
      await loadDomainStatus();
    } catch (error) {
      console.error('Error setting custom domain:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to set custom domain';
      addNotification('error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Remove custom domain
  const handleRemoveCustomDomain = async () => {
    if (!window.confirm('Are you sure you want to remove your custom domain?')) return;

    try {
      setSaving(true);
      await axios.delete(`${API_BASE_URL}/api/ecommerce/storefront/domain/domain`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setCustomDomain('');
      setDnsInstructions(null);
      addNotification('success', 'Custom domain removed');
      await loadDomainStatus();
    } catch (error) {
      console.error('Error removing custom domain:', error);
      addNotification('error', 'Failed to remove custom domain');
    } finally {
      setSaving(false);
    }
  };

  // Load DNS instructions
  const handleLoadDnsInstructions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/storefront/domain/domain/instructions`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setDnsInstructions(response.data);
    } catch (error) {
      console.error('Error loading DNS instructions:', error);
      addNotification('error', 'Failed to load DNS instructions');
    }
  };

  // Verify domain
  const handleVerifyDomain = async () => {
    try {
      setVerifying(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/ecommerce/storefront/domain/domain/verify`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.verified) {
        addNotification('success', 'Domain verified successfully!');
      } else {
        addNotification('warning', response.data.error || 'Domain verification failed. Please check your DNS records.');
      }
      await loadDomainStatus();
    } catch (error) {
      console.error('Error verifying domain:', error);
      const errorMessage = error.response?.data?.detail || 'Domain verification failed';
      addNotification('error', errorMessage);
    } finally {
      setVerifying(false);
    }
  };

  // Provision SSL certificate
  const handleProvisionSSL = async () => {
    try {
      setProvisioningSSL(true);
      await axios.post(
        `${API_BASE_URL}/api/ecommerce/storefront/domain/ssl/provision`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addNotification('success', 'SSL certificate provisioning started');
      await loadDomainStatus();
    } catch (error) {
      console.error('Error provisioning SSL:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to provision SSL certificate';
      addNotification('error', errorMessage);
    } finally {
      setProvisioningSSL(false);
    }
  };

  // Toggle publish status
  const handleTogglePublish = async () => {
    try {
      setSaving(true);
      if (domainStatus.is_published) {
        // Unpublish
        await axios.post(
          `${API_BASE_URL}/api/ecommerce/storefront/domain/publish`,
          { publish: false },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        addNotification('success', 'Store unpublished');
      } else {
        // Publish
        await axios.post(
          `${API_BASE_URL}/api/ecommerce/storefront/domain/publish`,
          { publish: true },
          { headers: { Authorization: `Bearer ${token}` } }
        );
        addNotification('success', 'Store published!');
      }
      await loadDomainStatus();
    } catch (error) {
      console.error('Error toggling publish status:', error);
      const errorMessage = error.response?.data?.detail || 'Failed to update publish status';
      addNotification('error', errorMessage);
    } finally {
      setSaving(false);
    }
  };

  // Toggle maintenance mode
  const handleToggleMaintenance = async () => {
    try {
      setSaving(true);
      await axios.post(
        `${API_BASE_URL}/api/ecommerce/storefront/domain/maintenance`,
        { enabled: !domainStatus.maintenance_mode },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addNotification(
        'success',
        domainStatus.maintenance_mode ? 'Maintenance mode disabled' : 'Maintenance mode enabled'
      );
      await loadDomainStatus();
    } catch (error) {
      console.error('Error toggling maintenance mode:', error);
      addNotification('error', 'Failed to update maintenance mode');
    } finally {
      setSaving(false);
    }
  };

  // Copy to clipboard
  const copyToClipboard = useCallback(
    text => {
      navigator.clipboard.writeText(text);
      addNotification('success', 'Copied to clipboard');
    },
    [addNotification]
  );

  // Open preview - uses path-based routing
  const handleOpenPreview = () => {
    let url;
    if (domainStatus.custom_domain && domainStatus.domain_verified) {
      url = `https://${domainStatus.custom_domain}`;
    } else if (domainStatus.subdomain) {
      // Use path-based URL: /store/{slug}
      url = `${STOREFRONT_BASE_URL}/store/${domainStatus.subdomain}`;
    } else {
      addNotification('warning', 'Please set up a store URL first');
      return;
    }
    window.open(url, '_blank');
  };

  // Get the store URL for display
  const getStoreUrl = () => {
    if (domainStatus.subdomain) {
      return `${STOREFRONT_BASE_URL}/store/${domainStatus.subdomain}`;
    }
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading domain settings...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-4xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="mb-6">
          <h1 className="text-2xl font-bold text-gray-900 flex items-center">
            <GlobeAltIcon className="w-8 h-8 mr-3 text-sage-600" />
            Domain Settings
          </h1>
          <p className="text-gray-600">Configure your storefront domain and publish your store</p>
        </div>

        {/* Status Overview */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Status Overview</h2>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <StatusCard
              label="Store URL"
              value={domainStatus.subdomain ? `/store/${domainStatus.subdomain}` : 'Not set'}
              status={domainStatus.subdomain ? 'success' : 'pending'}
            />
            <StatusCard
              label="Custom Domain"
              value={domainStatus.custom_domain || 'Not set'}
              status={domainStatus.custom_domain ? (domainStatus.domain_verified ? 'success' : 'warning') : 'pending'}
            />
            <StatusCard
              label="SSL Certificate"
              value={
                domainStatus.ssl_status === 'active'
                  ? 'Active'
                  : domainStatus.ssl_status === 'pending'
                    ? 'Pending'
                    : 'Not configured'
              }
              status={
                domainStatus.ssl_status === 'active'
                  ? 'success'
                  : domainStatus.ssl_status === 'pending'
                    ? 'warning'
                    : 'pending'
              }
            />
            <StatusCard
              label="Store Status"
              value={domainStatus.maintenance_mode ? 'Maintenance' : domainStatus.is_published ? 'Published' : 'Draft'}
              status={domainStatus.maintenance_mode ? 'warning' : domainStatus.is_published ? 'success' : 'pending'}
            />
          </div>
        </div>

        {/* Store URL Configuration */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
            <LinkIcon className="w-5 h-5 mr-2 text-gray-500" />
            Store URL
          </h2>
          <p className="text-sm text-gray-500 mb-4">
            Choose a unique URL for your store. This will be your store's address.
          </p>

          <div className="flex items-center space-x-2">
            <span className="px-4 py-2 bg-gray-100 border border-r-0 border-gray-300 rounded-l-md text-gray-600 text-sm">
              {STOREFRONT_BASE_URL}/store/
            </span>
            <input
              type="text"
              value={subdomain}
              onChange={e => {
                setSubdomain(e.target.value.toLowerCase());
                setSubdomainError(validateSubdomain(e.target.value.toLowerCase()));
              }}
              placeholder="myshop"
              className="flex-1 px-4 py-2 border border-gray-300 rounded-r-md focus:ring-sage-500 focus:border-sage-500"
            />
          </div>

          {subdomainError && <p className="mt-2 text-sm text-red-600">{subdomainError}</p>}

          <div className="flex items-center space-x-3 mt-4">
            <button
              onClick={handleSaveSubdomain}
              disabled={saving || !subdomain || subdomainError}
              className="px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : domainStatus.subdomain ? 'Update Store URL' : 'Save Store URL'}
            </button>
            {domainStatus.subdomain && (
              <button
                onClick={handleRemoveSubdomain}
                disabled={saving}
                className="px-4 py-2 text-red-600 hover:text-red-700"
              >
                Remove
              </button>
            )}
          </div>

          {/* Show full URL after saving */}
          {domainStatus.subdomain && (
            <div className="mt-4 p-3 bg-green-50 border border-green-200 rounded-lg">
              <p className="text-sm text-green-800">
                <strong>Your store URL:</strong>{' '}
                <a
                  href={getStoreUrl()}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="underline hover:text-green-900"
                >
                  {getStoreUrl()}
                </a>
              </p>
            </div>
          )}
        </div>

        {/* Custom Domain Configuration */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
            <GlobeAltIcon className="w-5 h-5 mr-2 text-gray-500" />
            Custom Domain
            <span className="ml-2 px-2 py-0.5 text-xs font-medium bg-amber-100 text-amber-800 rounded">Pro Plan</span>
          </h2>
          <p className="text-sm text-gray-500 mb-4">Connect your own domain for a professional branded storefront.</p>

          <div className="space-y-4">
            <div>
              <input
                type="text"
                value={customDomain}
                onChange={e => {
                  setCustomDomain(e.target.value.toLowerCase());
                  setCustomDomainError(validateCustomDomain(e.target.value.toLowerCase()));
                }}
                placeholder="shop.yourdomain.com"
                className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
              />
              {customDomainError && <p className="mt-2 text-sm text-red-600">{customDomainError}</p>}
            </div>

            <div className="flex items-center space-x-3">
              <button
                onClick={handleSetCustomDomain}
                disabled={saving || !customDomain || customDomainError}
                className="px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:bg-gray-400 disabled:cursor-not-allowed"
              >
                {saving ? 'Saving...' : domainStatus.custom_domain ? 'Update Domain' : 'Set Custom Domain'}
              </button>
              {domainStatus.custom_domain && (
                <>
                  <button onClick={handleLoadDnsInstructions} className="px-4 py-2 text-sage-600 hover:text-sage-700">
                    View DNS Instructions
                  </button>
                  <button
                    onClick={handleRemoveCustomDomain}
                    disabled={saving}
                    className="px-4 py-2 text-red-600 hover:text-red-700"
                  >
                    Remove
                  </button>
                </>
              )}
            </div>
          </div>

          {/* DNS Instructions */}
          {(dnsInstructions || domainStatus.custom_domain) && !domainStatus.domain_verified && (
            <div className="mt-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start">
                <InformationCircleIcon className="w-5 h-5 text-amber-600 mr-2 mt-0.5" />
                <div className="flex-1">
                  <h3 className="font-medium text-amber-800">DNS Configuration Required</h3>
                  <p className="text-sm text-amber-700 mt-1">Add the following DNS records to your domain provider:</p>

                  <div className="mt-4 space-y-3">
                    {/* CNAME Record */}
                    <div className="bg-white p-3 rounded border border-amber-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-500 uppercase">CNAME Record</span>
                        <button
                          onClick={() => copyToClipboard('stores.craftflow.store')}
                          className="text-amber-600 hover:text-amber-700"
                        >
                          <ClipboardDocumentIcon className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span> CNAME
                        </div>
                        <div>
                          <span className="text-gray-500">Name:</span> {customDomain?.split('.')[0] || 'shop'}
                        </div>
                        <div>
                          <span className="text-gray-500">Value:</span> stores.craftflow.store
                        </div>
                      </div>
                    </div>

                    {/* TXT Record */}
                    <div className="bg-white p-3 rounded border border-amber-200">
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-xs font-medium text-gray-500 uppercase">TXT Record (Verification)</span>
                        <button
                          onClick={() =>
                            copyToClipboard(
                              dnsInstructions?.verification_token || domainStatus.domain_verification_token || ''
                            )
                          }
                          className="text-amber-600 hover:text-amber-700"
                        >
                          <ClipboardDocumentIcon className="w-4 h-4" />
                        </button>
                      </div>
                      <div className="grid grid-cols-3 gap-2 text-sm">
                        <div>
                          <span className="text-gray-500">Type:</span> TXT
                        </div>
                        <div>
                          <span className="text-gray-500">Name:</span> _craftflow-verify
                        </div>
                        <div className="col-span-3 mt-1">
                          <span className="text-gray-500">Value:</span>{' '}
                          <code className="bg-gray-100 px-1 py-0.5 rounded text-xs break-all">
                            {dnsInstructions?.verification_token ||
                              domainStatus.domain_verification_token ||
                              'Loading...'}
                          </code>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="mt-4">
                    <button
                      onClick={handleVerifyDomain}
                      disabled={verifying}
                      className="flex items-center px-4 py-2 bg-amber-600 text-white rounded-md hover:bg-amber-700 disabled:bg-gray-400"
                    >
                      {verifying ? (
                        <>
                          <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                          Verifying...
                        </>
                      ) : (
                        <>
                          <CheckCircleIcon className="w-4 h-4 mr-2" />
                          Verify Domain
                        </>
                      )}
                    </button>
                    <p className="text-xs text-amber-700 mt-2">DNS changes can take up to 48 hours to propagate.</p>
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* Domain Verified */}
          {domainStatus.custom_domain && domainStatus.domain_verified && (
            <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
              <div className="flex items-center">
                <CheckCircleIcon className="w-5 h-5 text-green-600 mr-2" />
                <span className="text-green-800 font-medium">Domain verified successfully!</span>
              </div>
            </div>
          )}
        </div>

        {/* SSL Certificate */}
        {domainStatus.custom_domain && domainStatus.domain_verified && (
          <div className="bg-white rounded-lg shadow p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-2 flex items-center">
              <LockClosedIcon className="w-5 h-5 mr-2 text-gray-500" />
              SSL Certificate
            </h2>
            <p className="text-sm text-gray-500 mb-4">
              Secure your storefront with HTTPS. SSL certificates are automatically provisioned via Let's Encrypt.
            </p>

            <div className="flex items-center space-x-4">
              {domainStatus.ssl_status === 'active' ? (
                <div className="flex items-center text-green-600">
                  <ShieldCheckIcon className="w-5 h-5 mr-2" />
                  <span>SSL Active</span>
                  {domainStatus.ssl_expires_at && (
                    <span className="ml-2 text-sm text-gray-500">
                      (Expires: {new Date(domainStatus.ssl_expires_at).toLocaleDateString()})
                    </span>
                  )}
                </div>
              ) : domainStatus.ssl_status === 'pending' ? (
                <div className="flex items-center text-amber-600">
                  <ArrowPathIcon className="w-5 h-5 mr-2 animate-spin" />
                  <span>SSL Certificate Pending</span>
                </div>
              ) : (
                <button
                  onClick={handleProvisionSSL}
                  disabled={provisioningSSL}
                  className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:bg-gray-400"
                >
                  {provisioningSSL ? (
                    <>
                      <ArrowPathIcon className="w-4 h-4 mr-2 animate-spin" />
                      Provisioning...
                    </>
                  ) : (
                    <>
                      <ShieldCheckIcon className="w-4 h-4 mr-2" />
                      Provision SSL Certificate
                    </>
                  )}
                </button>
              )}
            </div>
          </div>
        )}

        {/* Publish Controls */}
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Store Visibility</h2>

          <div className="space-y-4">
            {/* Publish Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-medium text-gray-900">
                  {domainStatus.is_published ? 'Store is Published' : 'Store is Draft'}
                </h3>
                <p className="text-sm text-gray-500">
                  {domainStatus.is_published
                    ? 'Your store is live and visible to customers'
                    : 'Your store is not visible to customers'}
                </p>
              </div>
              <button
                onClick={handleTogglePublish}
                disabled={saving || (!domainStatus.subdomain && !domainStatus.custom_domain)}
                className={`flex items-center px-4 py-2 rounded-md ${
                  domainStatus.is_published
                    ? 'bg-gray-600 hover:bg-gray-700 text-white'
                    : 'bg-green-600 hover:bg-green-700 text-white'
                } disabled:bg-gray-400 disabled:cursor-not-allowed`}
              >
                {domainStatus.is_published ? (
                  <>
                    <EyeSlashIcon className="w-4 h-4 mr-2" />
                    Unpublish
                  </>
                ) : (
                  <>
                    <EyeIcon className="w-4 h-4 mr-2" />
                    Publish Store
                  </>
                )}
              </button>
            </div>

            {/* Maintenance Mode Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <h3 className="font-medium text-gray-900">Maintenance Mode</h3>
                <p className="text-sm text-gray-500">
                  {domainStatus.maintenance_mode
                    ? 'Store shows maintenance page to visitors'
                    : 'Store is accessible to visitors'}
                </p>
              </div>
              <button
                onClick={handleToggleMaintenance}
                disabled={saving}
                className={`flex items-center px-4 py-2 rounded-md ${
                  domainStatus.maintenance_mode
                    ? 'bg-amber-600 hover:bg-amber-700 text-white'
                    : 'bg-gray-200 hover:bg-gray-300 text-gray-700'
                }`}
              >
                <ExclamationTriangleIcon className="w-4 h-4 mr-2" />
                {domainStatus.maintenance_mode ? 'Disable Maintenance' : 'Enable Maintenance'}
              </button>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="flex items-center justify-between">
          <button
            onClick={() => navigate('/craftflow/settings')}
            className="px-4 py-2 text-gray-600 hover:text-gray-800"
          >
            Back to Settings
          </button>

          <div className="flex items-center space-x-3">
            <button
              onClick={loadDomainStatus}
              className="flex items-center px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              <ArrowPathIcon className="w-4 h-4 mr-2" />
              Refresh Status
            </button>

            {(domainStatus.subdomain || domainStatus.custom_domain) && (
              <button
                onClick={handleOpenPreview}
                className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
              >
                <EyeIcon className="w-4 h-4 mr-2" />
                Preview Store
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

// Status Card Component
const StatusCard = ({ label, value, status }) => {
  const getStatusColor = () => {
    switch (status) {
      case 'success':
        return 'bg-green-100 border-green-200 text-green-800';
      case 'warning':
        return 'bg-amber-100 border-amber-200 text-amber-800';
      case 'error':
        return 'bg-red-100 border-red-200 text-red-800';
      default:
        return 'bg-gray-100 border-gray-200 text-gray-600';
    }
  };

  const getIcon = () => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="w-4 h-4" />;
      case 'warning':
        return <ExclamationTriangleIcon className="w-4 h-4" />;
      case 'error':
        return <XCircleIcon className="w-4 h-4" />;
      default:
        return null;
    }
  };

  return (
    <div className={`p-3 rounded-lg border ${getStatusColor()}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium uppercase">{label}</span>
        {getIcon()}
      </div>
      <p className="mt-1 text-sm font-medium truncate" title={value}>
        {value}
      </p>
    </div>
  );
};

export default CraftFlowDomainSettings;
