import React, { useState } from 'react';
import { useSubscription } from '../hooks/useSubscription';
import { PricingTable, TierBadge, UsageIndicator } from '../components/subscription';

const SubscriptionPage = () => {
  const {
    currentTier,
    tierConfig,
    subscriptionActive,
    subscriptionExpiresAt,
    currentUsage,
    isFreeTier,
    isProTier,
    isPrintProTier,
    FEATURES,
    SUBSCRIPTION_TIERS,
  } = useSubscription();

  const [selectedPlan, setSelectedPlan] = useState(null);

  const handleSelectPlan = tierKey => {
    setSelectedPlan(tierKey);
    // TODO: Integrate with payment processor
    console.log(`Selected plan: ${tierKey}`);
  };

  const formatDate = dateString => {
    if (!dateString) return 'Never';
    return new Date(dateString).toLocaleDateString();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Current Subscription Status */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Subscription Management</h1>
              <div className="flex items-center space-x-3">
                <TierBadge size="large" showPrice />
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    subscriptionActive ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {subscriptionActive ? 'Active' : 'Inactive'}
                </span>
              </div>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-600">{subscriptionExpiresAt ? 'Next billing' : 'Status'}</p>
              <p className="font-medium text-gray-900">{formatDate(subscriptionExpiresAt)}</p>
            </div>
          </div>

          {/* Usage Overview for Free Tier */}
          {isFreeTier && (
            <div className="grid md:grid-cols-2 gap-6">
              <UsageIndicator feature={FEATURES.MOCKUP_GENERATOR} showDetails={true} />
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 className="font-medium text-blue-900 mb-2">Ready to upgrade?</h3>
                <p className="text-sm text-blue-800 mb-3">
                  Unlock unlimited mockups and premium features with our Pro plan.
                </p>
                <button
                  onClick={() => document.getElementById('pricing').scrollIntoView({ behavior: 'smooth' })}
                  className="bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors"
                >
                  View Plans
                </button>
              </div>
            </div>
          )}

          {/* Feature Summary */}
          <div className="mt-6 pt-6 border-t border-gray-200">
            <h3 className="font-medium text-gray-900 mb-3">What's included in your plan:</h3>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-3">
              {tierConfig &&
                Object.entries(tierConfig.features).map(
                  ([feature, enabled]) =>
                    enabled && (
                      <div key={feature} className="flex items-center text-sm">
                        <span className="text-green-500 mr-2">✓</span>
                        <span className="text-gray-700 capitalize">{feature.replace(/_/g, ' ')}</span>
                      </div>
                    )
                )}
            </div>
          </div>
        </div>

        {/* Usage Statistics for Non-Free Tiers */}
        {!isFreeTier && (
          <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Usage This Month</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <div className="text-3xl font-bold text-blue-600 mb-1">{currentUsage.mockupsThisMonth}</div>
                <div className="text-sm text-gray-600">Mockups Created</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-green-600 mb-1">{currentUsage.shopsConnected || 1}</div>
                <div className="text-sm text-gray-600">Shops Connected</div>
              </div>
              <div className="text-center">
                <div className="text-3xl font-bold text-purple-600 mb-1">{currentUsage.usersInOrg || 1}</div>
                <div className="text-sm text-gray-600">Team Members</div>
              </div>
            </div>
          </div>
        )}

        {/* Pricing Table */}
        <div id="pricing" className="bg-white rounded-xl shadow-sm border p-8">
          <PricingTable onSelectPlan={handleSelectPlan} highlightCurrent={true} />
        </div>

        {/* Feature Comparison */}
        <div className="bg-white rounded-xl shadow-sm border p-8 mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Feature Comparison</h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b">
                  <th className="text-left py-4 px-6">Feature</th>
                  <th className="text-center py-4 px-6">
                    <TierBadge tier={SUBSCRIPTION_TIERS.FREE} />
                  </th>
                  <th className="text-center py-4 px-6">
                    <TierBadge tier={SUBSCRIPTION_TIERS.PRO} />
                  </th>
                  <th className="text-center py-4 px-6">
                    <TierBadge tier={SUBSCRIPTION_TIERS.PRINT_PRO} />
                  </th>
                </tr>
              </thead>
              <tbody>
                {[
                  { name: 'Etsy Dashboard & Analytics', free: true, pro: true, printPro: true },
                  { name: 'Mockup Generator', free: '50/month', pro: 'Unlimited', printPro: 'Unlimited' },
                  { name: 'File Cleaner', free: true, pro: true, printPro: true },
                  { name: 'Listing Templates', free: false, pro: true, printPro: true },
                  { name: 'Auto-naming', free: false, pro: true, printPro: true },
                  { name: 'Batch Uploads', free: false, pro: true, printPro: true },
                  { name: 'File Resizing', free: false, pro: true, printPro: true },
                  { name: 'Print File Generator', free: false, pro: false, printPro: true },
                  { name: 'Advanced Resizing (DTF/Sublimation)', free: false, pro: false, printPro: true },
                  { name: 'CSV/Excel Export', free: false, pro: false, printPro: true },
                  { name: 'Multi-shop Support', free: false, pro: false, printPro: true },
                ].map((feature, index) => (
                  <tr key={index} className="border-b border-gray-100">
                    <td className="py-4 px-6 font-medium text-gray-900">{feature.name}</td>
                    <td className="py-4 px-6 text-center">
                      {feature.free === true ? (
                        <span className="text-green-500">✓</span>
                      ) : feature.free === false ? (
                        <span className="text-gray-300">✕</span>
                      ) : (
                        <span className="text-sm text-gray-600">{feature.free}</span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-center">
                      {feature.pro === true ? (
                        <span className="text-green-500">✓</span>
                      ) : feature.pro === false ? (
                        <span className="text-gray-300">✕</span>
                      ) : (
                        <span className="text-sm text-gray-600">{feature.pro}</span>
                      )}
                    </td>
                    <td className="py-4 px-6 text-center">
                      {feature.printPro === true ? (
                        <span className="text-green-500">✓</span>
                      ) : feature.printPro === false ? (
                        <span className="text-gray-300">✕</span>
                      ) : (
                        <span className="text-sm text-gray-600">{feature.printPro}</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="bg-white rounded-xl shadow-sm border p-8 mt-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Frequently Asked Questions</h2>
          <div className="space-y-6">
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Can I change plans at any time?</h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately, and billing is
                prorated.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">
                What happens if I exceed my mockup limit on the Free plan?
              </h3>
              <p className="text-gray-600">
                You'll need to wait until the next month or upgrade to Pro for unlimited mockups. Your existing mockups
                remain accessible.
              </p>
            </div>
            <div>
              <h3 className="font-semibold text-gray-900 mb-2">Is there a money-back guarantee?</h3>
              <p className="text-gray-600">
                Yes! We offer a 30-day money-back guarantee on all paid plans. Cancel within 30 days for a full refund.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;
