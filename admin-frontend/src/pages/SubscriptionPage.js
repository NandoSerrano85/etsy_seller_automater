import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import subscriptionService from '../services/subscriptionService';
import { TierBadge } from '../components/subscription';

// Initialize Stripe with your publishable key
const stripePromise = loadStripe(process.REACT_APP_STRIPE_PUBLISHABLE_KEY);

const SubscriptionPage = () => {
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [tiers, setTiers] = useState([]);
  const [billingHistory, setBillingHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingCheckout, setProcessingCheckout] = useState(false);
  const [error, setError] = useState(null);

  // Fetch subscription data
  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subscription, tiersData, history] = await Promise.all([
        subscriptionService.getCurrentSubscription(),
        subscriptionService.getSubscriptionTiers(),
        subscriptionService.getBillingHistory(10),
      ]);

      setCurrentSubscription(subscription);
      setTiers(tiersData.tiers || []);
      setBillingHistory(history || []);
    } catch (err) {
      console.error('Error fetching subscription data:', err);
      setError('Failed to load subscription data. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubscribe = async priceId => {
    try {
      setProcessingCheckout(true);
      setError(null);

      const stripe = await stripePromise;

      // Create checkout session
      const { session_id } = await subscriptionService.createCheckoutSession(
        priceId,
        `${window.location.origin}/subscription?success=true`,
        `${window.location.origin}/subscription?canceled=true`
      );

      // Redirect to Stripe Checkout
      const result = await stripe.redirectToCheckout({ sessionId: session_id });

      if (result.error) {
        setError(result.error.message);
      }
    } catch (err) {
      console.error('Error during checkout:', err);
      setError('Failed to start checkout. Please try again.');
    } finally {
      setProcessingCheckout(false);
    }
  };

  const handleUpgrade = async newPriceId => {
    if (!window.confirm('Are you sure you want to change your subscription plan?')) {
      return;
    }

    try {
      setProcessingCheckout(true);
      setError(null);

      await subscriptionService.updateSubscription(newPriceId);
      await fetchSubscriptionData();

      alert('Subscription updated successfully!');
    } catch (err) {
      console.error('Error upgrading subscription:', err);
      setError('Failed to upgrade subscription. Please try again.');
    } finally {
      setProcessingCheckout(false);
    }
  };

  const handleCancelSubscription = async () => {
    if (
      !window.confirm(
        'Are you sure you want to cancel your subscription? You will retain access until the end of your billing period.'
      )
    ) {
      return;
    }

    try {
      setProcessingCheckout(true);
      setError(null);

      await subscriptionService.cancelSubscription(false);
      await fetchSubscriptionData();

      alert('Subscription canceled. You will retain access until the end of your billing period.');
    } catch (err) {
      console.error('Error canceling subscription:', err);
      setError('Failed to cancel subscription. Please try again.');
    } finally {
      setProcessingCheckout(false);
    }
  };

  const handleManageBilling = async () => {
    try {
      setProcessingCheckout(true);
      setError(null);

      const { url } = await subscriptionService.createCustomerPortal(window.location.href);

      // Redirect to Stripe customer portal
      window.location.href = url;
    } catch (err) {
      console.error('Error opening customer portal:', err);
      setError('Failed to open billing portal. Please try again.');
    } finally {
      setProcessingCheckout(false);
    }
  };

  const formatDate = dateString => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const formatCurrency = amount => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  const isFreeTier = currentSubscription?.tier === 'free';
  const hasActiveSubscription = currentSubscription?.status === 'active' && !isFreeTier;

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Success/Error Messages */}
        {new URLSearchParams(window.location.search).get('success') === 'true' && (
          <div className="bg-green-50 border border-green-200 text-green-800 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Subscription activated successfully!</p>
          </div>
        )}

        {new URLSearchParams(window.location.search).get('canceled') === 'true' && (
          <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">Checkout canceled. No charges were made.</p>
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-lg mb-6">
            <p className="font-medium">{error}</p>
          </div>
        )}

        {/* Current Subscription Status */}
        <div className="bg-white rounded-xl shadow-sm border p-6 mb-8">
          <div className="flex items-center justify-between mb-6">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Subscription Management</h1>
              <div className="flex items-center space-x-3">
                <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-blue-100 text-blue-800">
                  {currentSubscription?.tier?.toUpperCase() || 'FREE'}
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-sm font-medium ${
                    currentSubscription?.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
                  }`}
                >
                  {currentSubscription?.status?.toUpperCase() || 'ACTIVE'}
                </span>
                {currentSubscription?.cancel_at_period_end && (
                  <span className="px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-700">
                    CANCELING AT PERIOD END
                  </span>
                )}
              </div>
            </div>
            {hasActiveSubscription && (
              <div className="text-right">
                <p className="text-sm text-gray-600">Next billing date</p>
                <p className="font-medium text-gray-900">{formatDate(currentSubscription?.current_period_end)}</p>
              </div>
            )}
          </div>

          {/* Action Buttons */}
          {hasActiveSubscription && (
            <div className="flex gap-3 pt-4 border-t border-gray-200">
              <button
                onClick={handleManageBilling}
                disabled={processingCheckout}
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
              >
                Manage Billing
              </button>
              {!currentSubscription?.cancel_at_period_end && (
                <button
                  onClick={handleCancelSubscription}
                  disabled={processingCheckout}
                  className="px-4 py-2 bg-red-50 text-red-700 rounded-lg hover:bg-red-100 disabled:bg-gray-100 transition-colors"
                >
                  Cancel Subscription
                </button>
              )}
            </div>
          )}
        </div>

        {/* Pricing Plans */}
        <div className="bg-white rounded-xl shadow-sm border p-8 mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Choose Your Plan</h2>
          <div className="grid md:grid-cols-3 gap-6">
            {tiers.map(tier => {
              const isCurrentTier = tier.id === currentSubscription?.tier;
              const isFree = tier.id === 'free';

              return (
                <div
                  key={tier.id}
                  className={`border-2 rounded-xl p-6 ${
                    isCurrentTier ? 'border-blue-600 bg-blue-50' : 'border-gray-200'
                  }`}
                >
                  <div className="text-center mb-6">
                    <h3 className="text-2xl font-bold text-gray-900 mb-2">{tier.name}</h3>
                    <div className="text-4xl font-bold text-gray-900 mb-1">
                      {formatCurrency(tier.price)}
                      <span className="text-lg font-normal text-gray-600">/month</span>
                    </div>
                  </div>

                  <ul className="space-y-3 mb-6">
                    {Object.entries(tier.features).map(([feature, value]) => (
                      <li key={feature} className="flex items-start text-sm">
                        <span className="text-green-500 mr-2 mt-0.5">✓</span>
                        <span className="text-gray-700">
                          {feature.replace(/_/g, ' ')}
                          {feature === 'monthly_mockup_limit' && value !== -1 ? `: ${value}/month` : ''}
                          {feature === 'monthly_mockup_limit' && value === -1 ? ': Unlimited' : ''}
                        </span>
                      </li>
                    ))}
                  </ul>

                  {isCurrentTier ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-500 rounded-lg font-medium cursor-not-allowed"
                    >
                      Current Plan
                    </button>
                  ) : isFree ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-500 rounded-lg font-medium cursor-not-allowed"
                    >
                      Free Plan
                    </button>
                  ) : hasActiveSubscription ? (
                    <button
                      onClick={() => handleUpgrade(tier.stripe_price_id)}
                      disabled={processingCheckout}
                      className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                      {processingCheckout ? 'Processing...' : 'Change Plan'}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSubscribe(tier.stripe_price_id)}
                      disabled={processingCheckout}
                      className="w-full py-3 px-4 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 disabled:bg-gray-400 transition-colors"
                    >
                      {processingCheckout ? 'Processing...' : 'Subscribe Now'}
                    </button>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* Billing History */}
        {hasActiveSubscription && billingHistory.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border p-8">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Billing History</h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Date</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Description</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Amount</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Status</th>
                    <th className="text-left py-3 px-4 font-medium text-gray-700">Invoice</th>
                  </tr>
                </thead>
                <tbody>
                  {billingHistory.map(item => (
                    <tr key={item.id} className="border-b last:border-0">
                      <td className="py-3 px-4">{formatDate(item.invoice_date)}</td>
                      <td className="py-3 px-4">{item.description || 'Subscription payment'}</td>
                      <td className="py-3 px-4 font-medium">{formatCurrency(item.amount)}</td>
                      <td className="py-3 px-4">
                        <span
                          className={`px-2 py-1 rounded-full text-xs font-medium ${
                            item.status === 'paid'
                              ? 'bg-green-100 text-green-700'
                              : item.status === 'failed'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                          }`}
                        >
                          {item.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="py-3 px-4">
                        {item.invoice_pdf_url && (
                          <a
                            href={item.invoice_pdf_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-blue-600 hover:text-blue-700 text-sm"
                          >
                            Download
                          </a>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SubscriptionPage;
