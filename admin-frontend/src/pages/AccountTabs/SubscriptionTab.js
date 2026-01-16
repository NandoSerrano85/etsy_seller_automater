import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import subscriptionService from '../../services/subscriptionService';
import { useNotifications } from '../../components/NotificationSystem';

const SubscriptionTab = () => {
  const [subscription, setSubscription] = useState(null);
  const [usageStats, setUsageStats] = useState(null);
  const [billingHistory, setBillingHistory] = useState([]);
  const [tiers, setTiers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showBillingDetail, setShowBillingDetail] = useState(null);
  const [showAllHistory, setShowAllHistory] = useState(false);
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    try {
      setLoading(true);
      const [subResponse, usageResponse, historyResponse, tiersResponse] = await Promise.all([
        subscriptionService.getCurrentSubscription().catch(() => null),
        subscriptionService.getUsageStats().catch(() => null),
        subscriptionService.getBillingHistory(12).catch(() => []), // Get up to 12 months
        subscriptionService.getSubscriptionTiers().catch(() => ({ tiers: [] })),
      ]);

      setSubscription(subResponse);
      setUsageStats(usageResponse);
      setBillingHistory(historyResponse || []);
      setTiers(tiersResponse?.tiers || []);
    } catch (error) {
      console.error('Error fetching subscription data:', error);
      addNotification({
        type: 'error',
        message: 'Failed to load subscription data',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleUpgrade = () => {
    navigate('/subscription');
  };

  const handleManageBilling = async () => {
    try {
      const response = await subscriptionService.createCustomerPortal(window.location.href);
      if (response?.url) {
        window.location.href = response.url;
      }
    } catch (error) {
      addNotification({
        type: 'error',
        message: 'Failed to open billing portal',
      });
    }
  };

  // Calculate next billing date as 1st of next month
  const getNextBillingDate = () => {
    if (usageStats?.next_billing_date) {
      return new Date(usageStats.next_billing_date);
    }
    const now = new Date();
    return new Date(now.getFullYear(), now.getMonth() + 1, 1);
  };

  const formatDate = dateString => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatMonth = dateString => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
    });
  };

  const getCurrentTierConfig = () => {
    const tierName = subscription?.tier || usageStats?.tier || 'free';
    return tiers.find(t => t.id === tierName) || { name: 'Free', price: 0, features: {} };
  };

  const getUsagePercentage = (current, limit) => {
    if (limit === -1) return 100; // Unlimited
    if (limit === 0) return 0;
    return Math.min(100, (current / limit) * 100);
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

  const currentTier = getCurrentTierConfig();
  const nextBilling = getNextBillingDate();
  const mockupsLimit = usageStats?.mockups_limit ?? currentTier?.limits?.monthly_mockups ?? -1;

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
                {currentTier.name}
                <span
                  className={`ml-2 px-2 py-1 text-xs font-medium rounded-full ${
                    subscription?.status === 'active' ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {subscription?.status || 'active'}
                </span>
              </span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sage-600">Amount</span>
              <span className="font-medium text-sage-900">${currentTier.price}/month</span>
            </div>

            <div className="flex items-center justify-between">
              <span className="text-sage-600">Next Billing</span>
              <span className="font-medium text-sage-900">{formatDate(nextBilling)}</span>
            </div>
          </div>

          <div className="mt-6 flex space-x-3">
            <button
              onClick={handleUpgrade}
              className="flex-1 bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium transition-colors"
            >
              {subscription?.tier === 'full' ? 'View Plans' : 'Upgrade Plan'}
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
            {currentTier.features &&
              Object.entries(currentTier.features)
                .filter(([key, value]) => value === true && !key.includes('limit') && !key.includes('max'))
                .slice(0, 6)
                .map(([key]) => (
                  <li key={key} className="flex items-center text-sage-700">
                    <svg
                      className="w-5 h-5 text-green-500 mr-3 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}
                  </li>
                ))}
          </ul>
        </div>
      </div>

      {/* Usage Stats */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <h3 className="text-lg font-semibold text-sage-900 mb-4">Usage This Month</h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-sage-900">{usageStats?.mockups_created ?? 0}</div>
            <div className="text-sage-600 text-sm mt-1">Mockups Created</div>
            <div className="w-full bg-sage-200 rounded-full h-2 mt-3">
              <div
                className="bg-sage-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${getUsagePercentage(usageStats?.mockups_created ?? 0, mockupsLimit)}%` }}
              ></div>
            </div>
            <div className="text-xs text-sage-500 mt-1">
              {mockupsLimit === -1 ? 'Unlimited' : `${usageStats?.mockups_created ?? 0} / ${mockupsLimit}`}
            </div>
          </div>

          <div className="text-center p-4 bg-gray-50 rounded-lg">
            <div className="text-3xl font-bold text-sage-900">{usageStats?.designs_uploaded ?? 0}</div>
            <div className="text-sage-600 text-sm mt-1">Designs Uploaded</div>
            <div className="w-full bg-sage-200 rounded-full h-2 mt-3">
              <div className="bg-blue-500 h-2 rounded-full" style={{ width: '100%' }}></div>
            </div>
            <div className="text-xs text-sage-500 mt-1">Unlimited</div>
          </div>
        </div>

        <div className="mt-4 p-3 bg-blue-50 rounded-lg">
          <p className="text-sm text-blue-700">
            <span className="font-medium">Billing Cycle:</span> Your usage resets on the 1st of each month. Next reset:{' '}
            {formatDate(nextBilling)}
          </p>
        </div>
      </div>

      {/* Billing History */}
      <div className="bg-white rounded-lg shadow-sm border border-sage-200 p-6">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-semibold text-sage-900">Billing History</h3>
          {billingHistory.length > 3 && (
            <button
              onClick={() => setShowAllHistory(!showAllHistory)}
              className="text-sage-600 hover:text-sage-700 text-sm font-medium"
            >
              {showAllHistory ? 'Show Less' : 'View All'}
            </button>
          )}
        </div>

        {billingHistory.length === 0 ? (
          <div className="text-center py-8 text-sage-500">
            <svg className="w-12 h-12 mx-auto mb-3 text-sage-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
            <p>No billing history yet</p>
          </div>
        ) : (
          <div className="space-y-3">
            {(showAllHistory ? billingHistory : billingHistory.slice(0, 3)).map(item => (
              <div
                key={item.id}
                className="flex items-center justify-between py-3 border-b border-sage-100 last:border-0 cursor-pointer hover:bg-sage-50 rounded-lg px-3 -mx-3 transition-colors"
                onClick={() => setShowBillingDetail(item)}
              >
                <div>
                  <div className="font-medium text-sage-900">{formatMonth(item.invoice_date)}</div>
                  <div className="text-sm text-sage-600">{subscription?.tier || 'Subscription'} Plan</div>
                </div>
                <div className="text-right flex items-center space-x-4">
                  <div>
                    <div className="font-medium text-sage-900">
                      ${typeof item.amount === 'number' ? item.amount.toFixed(2) : item.amount}
                    </div>
                    <div className={`text-sm ${item.status === 'paid' ? 'text-green-600' : 'text-yellow-600'}`}>
                      {item.status?.charAt(0).toUpperCase() + item.status?.slice(1)}
                    </div>
                  </div>
                  <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Billing Detail Modal */}
      {showBillingDetail && (
        <BillingDetailModal billing={showBillingDetail} onClose={() => setShowBillingDetail(null)} />
      )}
    </div>
  );
};

// Billing Detail Modal Component
const BillingDetailModal = ({ billing, onClose }) => {
  const formatDate = dateString => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl shadow-xl max-w-lg w-full mx-4 overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-sage-500 to-sage-600 p-6 text-white">
          <div className="flex justify-between items-start">
            <div>
              <h3 className="text-xl font-bold">Invoice Details</h3>
              <p className="text-sage-100 mt-1">{formatDate(billing.invoice_date)}</p>
            </div>
            <button onClick={onClose} className="text-white hover:text-sage-200 transition-colors">
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="p-6 space-y-6">
          {/* Amount */}
          <div className="text-center py-4 bg-gray-50 rounded-lg">
            <div className="text-4xl font-bold text-sage-900">
              ${typeof billing.amount === 'number' ? billing.amount.toFixed(2) : billing.amount}
            </div>
            <div className="text-sage-600 mt-1">{billing.currency?.toUpperCase() || 'USD'}</div>
          </div>

          {/* Details */}
          <div className="space-y-4">
            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sage-600">Status</span>
              <span
                className={`font-medium px-2 py-1 rounded-full text-sm ${
                  billing.status === 'paid' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                }`}
              >
                {billing.status?.charAt(0).toUpperCase() + billing.status?.slice(1)}
              </span>
            </div>

            <div className="flex justify-between py-2 border-b border-gray-100">
              <span className="text-sage-600">Invoice Date</span>
              <span className="font-medium text-sage-900">{formatDate(billing.invoice_date)}</span>
            </div>

            {billing.paid_at && (
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-sage-600">Paid Date</span>
                <span className="font-medium text-sage-900">{formatDate(billing.paid_at)}</span>
              </div>
            )}

            {billing.description && (
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-sage-600">Description</span>
                <span className="font-medium text-sage-900">{billing.description}</span>
              </div>
            )}

            {billing.stripe_invoice_id && (
              <div className="flex justify-between py-2 border-b border-gray-100">
                <span className="text-sage-600">Invoice ID</span>
                <span className="font-medium text-sage-900 text-sm">{billing.stripe_invoice_id}</span>
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex space-x-3">
            {billing.invoice_pdf_url && (
              <a
                href={billing.invoice_pdf_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 bg-sage-600 hover:bg-sage-700 text-white px-4 py-2 rounded-lg font-medium text-center transition-colors"
              >
                Download PDF
              </a>
            )}
            {billing.hosted_invoice_url && (
              <a
                href={billing.hosted_invoice_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex-1 border border-sage-300 hover:border-sage-400 text-sage-700 px-4 py-2 rounded-lg font-medium text-center transition-colors"
              >
                View Online
              </a>
            )}
          </div>

          <button
            onClick={onClose}
            className="w-full border border-gray-300 text-gray-700 px-4 py-2 rounded-lg font-medium hover:bg-gray-50 transition-colors"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionTab;
