'use client';

import { useState } from 'react';
import StepModal from '@/components/modals/StepModal';

type Tab = 'organization' | 'printers' | 'integrations' | 'team';

interface Printer {
  id: string;
  name: string;
  type: string;
  status: 'online' | 'offline';
}

export default function AccountPage() {
  const [activeTab, setActiveTab] = useState<Tab>('organization');
  const [isAddPrinterModalOpen, setIsAddPrinterModalOpen] =
    useState<boolean>(false);
  const [integrations, setIntegrations] = useState({
    etsy: { connected: false, loading: false },
    shopify: { connected: false, loading: false },
  });
  const [authUrl, setAuthUrl] = useState<string>('');

  const tabs = [
    { id: 'organization', label: 'Organization', key: 'organization' as Tab },
    { id: 'printers', label: 'Printers', key: 'printers' as Tab },
    { id: 'integrations', label: 'Integrations', key: 'integrations' as Tab },
    { id: 'team', label: 'Team', key: 'team' as Tab },
  ];

  const printers: Printer[] = [
    { id: '1', name: 'Main Printer', type: 'Canon PIXMA', status: 'online' },
    { id: '2', name: 'Backup Printer', type: 'HP LaserJet', status: 'offline' },
  ];

  const handleConnectEtsy = async () => {
    setIntegrations((prev) => ({
      ...prev,
      etsy: { ...prev.etsy, loading: true },
    }));

    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/oauth-data`
      );
      const data = await response.json();
      setAuthUrl(data.authUrl);
      // Simulate connection after getting auth URL
      setTimeout(() => {
        setIntegrations((prev) => ({
          ...prev,
          etsy: { connected: true, loading: false },
        }));
      }, 1000);
    } catch (error) {
      console.error('Error connecting to Etsy:', error);
      setIntegrations((prev) => ({
        ...prev,
        etsy: { ...prev.etsy, loading: false },
      }));
    }
  };

  const handleConnectShopify = async () => {
    setIntegrations((prev) => ({
      ...prev,
      shopify: { ...prev.shopify, loading: true },
    }));

    try {
      // Simulate Shopify OAuth flow
      const shopifyUrl = `https://your-shop.myshopify.com/admin/oauth/authorize?client_id=your_client_id&scope=read_products,write_products&redirect_uri=${encodeURIComponent(window.location.origin)}/api/shopify/callback`;

      // Open in new window for OAuth
      window.open(shopifyUrl, '_blank', 'width=500,height=600');

      // Simulate successful connection
      setTimeout(() => {
        setIntegrations((prev) => ({
          ...prev,
          shopify: { connected: true, loading: false },
        }));
      }, 3000);
    } catch (error) {
      console.error('Error connecting to Shopify:', error);
      setIntegrations((prev) => ({
        ...prev,
        shopify: { ...prev.shopify, loading: false },
      }));
    }
  };

  const handleDisconnectEtsy = () => {
    setIntegrations((prev) => ({
      ...prev,
      etsy: { connected: false, loading: false },
    }));
    setAuthUrl('');
  };

  const handleDisconnectShopify = () => {
    setIntegrations((prev) => ({
      ...prev,
      shopify: { connected: false, loading: false },
    }));
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 'organization':
        return (
          <div className="space-y-6">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Organization Name
              </label>
              <input
                type="text"
                className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary"
                placeholder="Your Organization"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Business Type
              </label>
              <select className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary">
                <option>Individual</option>
                <option>Small Business</option>
                <option>Enterprise</option>
              </select>
            </div>
            <button className="bg-primary text-white px-4 py-2 rounded-md hover:bg-opacity-90">
              Save Changes
            </button>
          </div>
        );

      case 'printers':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Manage Printers</h3>
              <button
                onClick={() => setIsAddPrinterModalOpen(true)}
                className="bg-primary text-white px-4 py-2 rounded-md hover:bg-opacity-90"
              >
                Add Printer
              </button>
            </div>

            <div className="space-y-4">
              {printers.map((printer) => (
                <div
                  key={printer.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                >
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {printer.name}
                    </h4>
                    <p className="text-sm text-gray-500">{printer.type}</p>
                  </div>
                  <div className="flex items-center space-x-3">
                    <span
                      className={`inline-flex px-2 py-1 text-xs font-semibold rounded-full ${
                        printer.status === 'online'
                          ? 'bg-green-100 text-green-800'
                          : 'bg-red-100 text-red-800'
                      }`}
                    >
                      {printer.status}
                    </span>
                    <button className="text-gray-400 hover:text-gray-600">
                      <svg
                        className="w-5 h-5"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                        />
                      </svg>
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        );

      case 'integrations':
        return (
          <div className="space-y-6">
            <h3 className="text-lg font-medium">Connected Integrations</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Etsy Integration */}
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-orange-500 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">E</span>
                    </div>
                    <div>
                      <h4 className="font-medium">Etsy</h4>
                      <p className="text-sm text-gray-500">
                        {integrations.etsy.loading
                          ? 'Connecting...'
                          : integrations.etsy.connected
                            ? 'Connected'
                            : 'Not connected'}
                      </p>
                    </div>
                  </div>
                  {integrations.etsy.connected ? (
                    <button
                      onClick={handleDisconnectEtsy}
                      className="text-red-600 text-sm hover:text-red-800"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={handleConnectEtsy}
                      disabled={integrations.etsy.loading}
                      className="text-primary text-sm hover:text-opacity-80 disabled:opacity-50"
                    >
                      {integrations.etsy.loading ? 'Connecting...' : 'Connect'}
                    </button>
                  )}
                </div>

                {authUrl && !integrations.etsy.connected && (
                  <div className="mt-3 p-3 bg-orange-50 border border-orange-200 rounded">
                    <p className="text-xs text-orange-800 mb-2">
                      Click to authorize with Etsy:
                    </p>
                    <a
                      href={authUrl}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-xs text-primary underline hover:text-opacity-80 break-all"
                    >
                      {authUrl}
                    </a>
                  </div>
                )}
              </div>

              {/* Shopify Integration */}
              <div className="p-4 border border-gray-200 rounded-lg">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-8 h-8 bg-green-600 rounded flex items-center justify-center">
                      <span className="text-white text-xs font-bold">S</span>
                    </div>
                    <div>
                      <h4 className="font-medium">Shopify</h4>
                      <p className="text-sm text-gray-500">
                        {integrations.shopify.loading
                          ? 'Connecting...'
                          : integrations.shopify.connected
                            ? 'Connected'
                            : 'Not connected'}
                      </p>
                    </div>
                  </div>
                  {integrations.shopify.connected ? (
                    <button
                      onClick={handleDisconnectShopify}
                      className="text-red-600 text-sm hover:text-red-800"
                    >
                      Disconnect
                    </button>
                  ) : (
                    <button
                      onClick={handleConnectShopify}
                      disabled={integrations.shopify.loading}
                      className="text-primary text-sm hover:text-opacity-80 disabled:opacity-50"
                    >
                      {integrations.shopify.loading
                        ? 'Connecting...'
                        : 'Connect'}
                    </button>
                  )}
                </div>

                {integrations.shopify.loading && (
                  <div className="mt-3 p-3 bg-green-50 border border-green-200 rounded">
                    <p className="text-xs text-green-800">
                      Opening Shopify authorization window...
                    </p>
                  </div>
                )}
              </div>
            </div>
          </div>
        );

      case 'team':
        return (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <h3 className="text-lg font-medium">Team Members</h3>
              <button className="bg-primary text-white px-4 py-2 rounded-md hover:bg-opacity-90">
                Invite Member
              </button>
            </div>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                <div>
                  <h4 className="font-medium text-gray-900">John Doe</h4>
                  <p className="text-sm text-gray-500">
                    john@example.com - Owner
                  </p>
                </div>
                <button className="text-gray-400 hover:text-gray-600">
                  <svg
                    className="w-5 h-5"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 5v.01M12 12v.01M12 19v.01M12 6a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2zm0 7a1 1 0 110-2 1 1 0 010 2z"
                    />
                  </svg>
                </button>
              </div>
            </div>
          </div>
        );

      default:
        return null;
    }
  };

  return (
    <div>
      <h1 className="text-3xl font-bold text-gray-900 mb-6">
        Account Settings
      </h1>

      <div className="border-b border-gray-200 mb-6">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.key)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab.key
                  ? 'border-primary text-primary'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      <div className="max-w-2xl">{renderTabContent()}</div>

      <StepModal
        open={isAddPrinterModalOpen}
        onOpenChange={setIsAddPrinterModalOpen}
        title="Add New Printer"
        steps={[
          <div key="step1">
            <h3 className="text-lg font-medium mb-4">Printer Information</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Printer Name
                </label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary"
                  placeholder="Enter printer name"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Printer Model
                </label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary"
                  placeholder="Enter printer model"
                />
              </div>
            </div>
          </div>,
          <div key="step2">
            <h3 className="text-lg font-medium mb-4">Connection Settings</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Connection Type
                </label>
                <select className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary">
                  <option>USB</option>
                  <option>Network</option>
                  <option>Wireless</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  IP Address (if network)
                </label>
                <input
                  type="text"
                  className="w-full p-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary focus:border-primary"
                  placeholder="192.168.1.100"
                />
              </div>
            </div>
          </div>,
        ]}
      />
    </div>
  );
}
