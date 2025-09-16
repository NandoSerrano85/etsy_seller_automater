import React, { useState, useEffect } from 'react';
import { useNotifications } from '../../components/NotificationSystem';

const SubscriptionTab = () => {
  const [subscriptionData, setSubscriptionData] = useState(null);
  const [loading, setLoading] = useState(true);
  const { addNotification } = useNotifications();

  useEffect(() => {
    // Mock subscription data - replace with actual API call
    setTimeout(() => {
      setSubscriptionData({
        plan: 'Pro',
        status: 'active',
        nextBillingDate: '2025-10-16',
        amount: 29.99,
        currency: 'USD',
        features: [
          'Unlimited design uploads',
          'Advanced organization management',
          'Priority printer support',
          'API access',
          'Custom integrations',
        ],
      });
      setLoading(false);
    }, 1000);
  }, []);

  const handleUpgrade = () => {
    addNotification({
      type: 'info',
      message: 'Subscription management coming soon!',
    });
  };

  const handleManageBilling = () => {
    addNotification({
      type: 'info',
      message: 'Billing management coming soon!',
    });
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="flex flex-col items-center space-y-4">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-sage-600"></div>
          <p className="text-sage-600">Loading subscription...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-sage-900">Subscription</h2>
        <p className="text-sage-600 mt-1">Manage your subscription and billing</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Plan */}
        <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
          <h3 className="text-lg font-semibold text-sage-900 mb-4">Current Plan</h3>

          <div className="space-y-4">
            <div className="flex items-center justify-between">
              <span className="text-sage-600">Plan</span>
              <span className="font-medium text-sage-900 flex items-center">
                {subscriptionData?.plan}
                <span className="ml-2 px-2 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                  {subscriptionData?.status}
                </span>
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sage-600">Amount</span>
              <span className="font-medium text-sage-900">
                ${subscriptionData?.amount}/{subscriptionData?.currency === 'USD' ? 'month' : 'month'}
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sage-600">Next Billing</span>
              <span className="font-medium text-sage-900">
                {new Date(subscriptionData?.nextBillingDate).toLocaleDateString()}
              </span>
            </div>
          </div>

          <div className="mt-6 flex space-x-3">
            <button
              onClick={handleUpgrade}
              className="flex-1 bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Upgrade Plan
            </button>
            <button
              onClick={handleManageBilling}
              className="flex-1 border border-sage-300 hover:border-sage-400 text-sage-700 px-4 py-2 rounded-lg font-medium transition-colors"
            >
              Manage Billing
            </button>
          </div>
        </div>

        {/* Plan Features */}
        <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
          <h3 className="text-lg font-semibold text-sage-900 mb-4">Plan Features</h3>

          <ul className="space-y-3">
            {subscriptionData?.features.map((feature, index) => (
              <li key={index} className="flex items-center text-sage-700">
                <svg
                  className="w-5 h-5 text-green-500 mr-3 flex-shrink-0"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                {feature}
              </li>
            ))}
          </ul>
        </div>
      </div>

      {/* Usage Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <h3 className="text-lg font-semibold text-sage-900 mb-4">Usage This Month</h3>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-sage-900">156</div>
            <div className="text-sage-600 text-sm">Designs Uploaded</div>
            <div className="w-full bg-sage-200 rounded-full h-2 mt-2">
              <div className="bg-sage-600 h-2 rounded-full" style={{ width: '65%' }}></div>
            </div>
            <div className="text-xs text-sage-500 mt-1">Unlimited</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-sage-900">23</div>
            <div className="text-sage-600 text-sm">Print Jobs</div>
            <div className="w-full bg-sage-200 rounded-full h-2 mt-2">
              <div className="bg-sage-600 h-2 rounded-full" style={{ width: '46%' }}></div>
            </div>
            <div className="text-xs text-sage-500 mt-1">Unlimited</div>
          </div>

          <div className="text-center">
            <div className="text-2xl font-bold text-sage-900">8</div>
            <div className="text-sage-600 text-sm">API Calls (thousands)</div>
            <div className="w-full bg-sage-200 rounded-full h-2 mt-2">
              <div className="bg-sage-600 h-2 rounded-full" style={{ width: '32%' }}></div>
            </div>
            <div className="text-xs text-sage-500 mt-1">25k limit</div>
          </div>
        </div>
      </div>

      {/* Billing History */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <h3 className="text-lg font-semibold text-sage-900 mb-4">Recent Billing History</h3>

        <div className="space-y-3">
          <div className="flex items-center justify-between py-2 border-b border-sage-100">
            <div>
              <div className="font-medium text-sage-900">September 2025</div>
              <div className="text-sm text-sage-600">Pro Plan</div>
            </div>
            <div className="text-right">
              <div className="font-medium text-sage-900">$29.99</div>
              <div className="text-sm text-green-600">Paid</div>
            </div>
          </div>

          <div className="flex items-center justify-between py-2 border-b border-sage-100">
            <div>
              <div className="font-medium text-sage-900">August 2025</div>
              <div className="text-sm text-sage-600">Pro Plan</div>
            </div>
            <div className="text-right">
              <div className="font-medium text-sage-900">$29.99</div>
              <div className="text-sm text-green-600">Paid</div>
            </div>
          </div>

          <div className="flex items-center justify-between py-2">
            <div>
              <div className="font-medium text-sage-900">July 2025</div>
              <div className="text-sm text-sage-600">Pro Plan</div>
            </div>
            <div className="text-right">
              <div className="font-medium text-sage-900">$29.99</div>
              <div className="text-sm text-green-600">Paid</div>
            </div>
          </div>
        </div>

        <button
          onClick={handleManageBilling}
          className="mt-4 text-sage-600 hover:text-sage-700 font-medium transition-colors"
        >
          View All Billing History →
        </button>
      </div>
    </div>
  );
};

export default SubscriptionTab;
