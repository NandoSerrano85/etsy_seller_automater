import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import subscriptionService from '../services/subscriptionService';

// Initialize Stripe with your publishable key
const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

// Feature descriptions for display
const FEATURE_LABELS = {
  mockup_generator: 'Mockup Generator',
  monthly_mockup_limit: 'Monthly Mockups',
  file_cleaner: 'File Cleaner',
  etsy_dashboard: 'Etsy Dashboard',
  listing_templates: 'Listing Templates',
  auto_naming: 'Auto Naming',
  batch_uploads: 'Batch Uploads',
  file_resizing: 'File Resizing',
  print_file_generator: 'Print File Generator',
  advanced_resizing: 'Advanced Resizing',
  csv_export: 'CSV Export',
  multi_shop_support: 'Multi-Shop Support',
};

const SubscriptionPage = () => {
  const [currentSubscription, setCurrentSubscription] = useState(null);
  const [tiers, setTiers] = useState([]);
  const [billingHistory, setBillingHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [processingCheckout, setProcessingCheckout] = useState(null);
  const [error, setError] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  // Check URL params for success/cancel
  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      setSuccessMessage('Subscription activated successfully! Welcome aboard.');
      // Clean URL
      window.history.replaceState({}, '', window.location.pathname);
    }
    if (params.get('canceled') === 'true') {
      setError('Checkout was canceled. No charges were made.');
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  // Fetch subscription data
  useEffect(() => {
    fetchSubscriptionData();
  }, []);

  const fetchSubscriptionData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [subscription, tiersData, history] = await Promise.all([
        subscriptionService.getCurrentSubscription().catch(() => null),
        subscriptionService.getSubscriptionTiers(),
        subscriptionService.getBillingHistory(10).catch(() => []),
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

  const handleSubscribe = async (tierId, priceId) => {
    if (!priceId) {
      setError('This plan is not available for purchase yet.');
      return;
    }

    try {
      setProcessingCheckout(tierId);
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
      setProcessingCheckout(null);
    }
  };

  const handleUpgrade = async (tierId, newPriceId) => {
    if (!window.confirm('Are you sure you want to change your subscription plan? Your billing will be prorated.')) {
      return;
    }

    try {
      setProcessingCheckout(tierId);
      setError(null);

      await subscriptionService.updateSubscription(newPriceId);
      await fetchSubscriptionData();

      setSuccessMessage('Subscription updated successfully!');
    } catch (err) {
      console.error('Error upgrading subscription:', err);
      setError('Failed to upgrade subscription. Please try again.');
    } finally {
      setProcessingCheckout(null);
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
      setProcessingCheckout('cancel');
      setError(null);

      await subscriptionService.cancelSubscription(false);
      await fetchSubscriptionData();

      setSuccessMessage('Subscription canceled. You will retain access until the end of your billing period.');
    } catch (err) {
      console.error('Error canceling subscription:', err);
      setError('Failed to cancel subscription. Please try again.');
    } finally {
      setProcessingCheckout(null);
    }
  };

  const handleManageBilling = async () => {
    try {
      setProcessingCheckout('billing');
      setError(null);

      const { url } = await subscriptionService.createCustomerPortal(window.location.href);
      window.location.href = url;
    } catch (err) {
      console.error('Error opening customer portal:', err);
      setError('Failed to open billing portal. Please try again.');
    } finally {
      setProcessingCheckout(null);
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

  const getTierColor = tierId => {
    const colors = {
      free: 'from-gray-500 to-gray-600',
      starter: 'from-blue-500 to-blue-600',
      pro: 'from-purple-500 to-purple-600',
      full: 'from-amber-500 to-orange-600',
    };
    return colors[tierId] || 'from-gray-500 to-gray-600';
  };

  const getTierBorderColor = (tierId, isCurrentTier) => {
    if (!isCurrentTier) return 'border-gray-200 hover:border-gray-300';
    const colors = {
      free: 'border-gray-400',
      starter: 'border-blue-500',
      pro: 'border-purple-500',
      full: 'border-amber-500',
    };
    return colors[tierId] || 'border-gray-400';
  };

  const getPopularBadge = tierId => {
    if (tierId === 'pro') return 'Most Popular';
    if (tierId === 'full') return 'Best Value';
    return null;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading subscription details...</p>
        </div>
      </div>
    );
  }

  const isFreeTier = !currentSubscription || currentSubscription?.tier === 'free';
  const hasActiveSubscription = currentSubscription?.status === 'active' && !isFreeTier;

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto px-4 py-12">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Unlock powerful features to grow your business. All plans include a 14-day money-back guarantee.
          </p>
        </div>

        {/* Messages */}
        {successMessage && (
          <div className="max-w-3xl mx-auto mb-8">
            <div className="bg-green-50 border border-green-200 text-green-800 px-6 py-4 rounded-xl flex items-center">
              <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="font-medium">{successMessage}</p>
              <button onClick={() => setSuccessMessage(null)} className="ml-auto text-green-600 hover:text-green-800">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}

        {error && (
          <div className="max-w-3xl mx-auto mb-8">
            <div className="bg-red-50 border border-red-200 text-red-800 px-6 py-4 rounded-xl flex items-center">
              <svg className="w-5 h-5 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                  clipRule="evenodd"
                />
              </svg>
              <p className="font-medium">{error}</p>
              <button onClick={() => setError(null)} className="ml-auto text-red-600 hover:text-red-800">
                <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z"
                    clipRule="evenodd"
                  />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* Current Subscription Banner */}
        {hasActiveSubscription && (
          <div className="max-w-3xl mx-auto mb-8">
            <div className="bg-white rounded-xl shadow-sm border p-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div
                    className={`w-12 h-12 rounded-xl bg-gradient-to-br ${getTierColor(currentSubscription.tier)} flex items-center justify-center`}
                  >
                    <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Current Plan</p>
                    <p className="text-xl font-bold text-gray-900 capitalize">{currentSubscription.tier}</p>
                  </div>
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">
                    {currentSubscription.cancel_at_period_end ? 'Access until' : 'Renews on'}
                  </p>
                  <p className="font-semibold text-gray-900">{formatDate(currentSubscription.current_period_end)}</p>
                </div>
              </div>
              <div className="flex gap-3 mt-4 pt-4 border-t">
                <button
                  onClick={handleManageBilling}
                  disabled={processingCheckout === 'billing'}
                  className="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 disabled:opacity-50 transition-colors text-sm font-medium"
                >
                  {processingCheckout === 'billing' ? 'Opening...' : 'Manage Billing'}
                </button>
                {!currentSubscription.cancel_at_period_end && (
                  <button
                    onClick={handleCancelSubscription}
                    disabled={processingCheckout === 'cancel'}
                    className="px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg disabled:opacity-50 transition-colors text-sm font-medium"
                  >
                    {processingCheckout === 'cancel' ? 'Canceling...' : 'Cancel Subscription'}
                  </button>
                )}
                {currentSubscription.cancel_at_period_end && (
                  <span className="px-4 py-2 text-amber-600 text-sm font-medium">Canceling at period end</span>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {tiers.map(tier => {
            const isCurrentTier = tier.id === currentSubscription?.tier;
            const isFree = tier.id === 'free';
            const popularBadge = getPopularBadge(tier.id);
            const isProcessing = processingCheckout === tier.id;

            return (
              <div
                key={tier.id}
                className={`relative bg-white rounded-2xl shadow-sm border-2 ${getTierBorderColor(tier.id, isCurrentTier)} transition-all duration-200 ${
                  isCurrentTier ? 'ring-2 ring-offset-2 ring-blue-500' : ''
                } ${popularBadge ? 'lg:-mt-4 lg:mb-4' : ''}`}
              >
                {/* Popular Badge */}
                {popularBadge && (
                  <div
                    className={`absolute -top-4 left-1/2 -translate-x-1/2 px-4 py-1 rounded-full text-white text-sm font-medium bg-gradient-to-r ${getTierColor(tier.id)}`}
                  >
                    {popularBadge}
                  </div>
                )}

                {/* Header */}
                <div className={`p-6 rounded-t-2xl bg-gradient-to-br ${getTierColor(tier.id)}`}>
                  <h3 className="text-xl font-bold text-white mb-1">{tier.name}</h3>
                  <div className="flex items-baseline">
                    <span className="text-4xl font-bold text-white">
                      {tier.price === 0 ? 'Free' : formatCurrency(tier.price)}
                    </span>
                    {tier.price > 0 && <span className="text-white/80 ml-2">/month</span>}
                  </div>
                </div>

                {/* Features */}
                <div className="p-6">
                  <ul className="space-y-3 mb-6">
                    {Object.entries(tier.features).map(([feature, value]) => {
                      if (value === false) return null;

                      let displayValue = '';
                      if (feature === 'monthly_mockup_limit') {
                        displayValue = value === -1 ? 'Unlimited mockups' : `${value} mockups/month`;
                      } else {
                        displayValue = FEATURE_LABELS[feature] || feature.replace(/_/g, ' ');
                      }

                      return (
                        <li key={feature} className="flex items-start text-sm">
                          <svg
                            className="w-5 h-5 text-green-500 mr-2 flex-shrink-0"
                            fill="currentColor"
                            viewBox="0 0 20 20"
                          >
                            <path
                              fillRule="evenodd"
                              d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                              clipRule="evenodd"
                            />
                          </svg>
                          <span className="text-gray-700 capitalize">{displayValue}</span>
                        </li>
                      );
                    })}
                  </ul>

                  {/* Action Button */}
                  {isCurrentTier ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-500 rounded-xl font-medium cursor-not-allowed"
                    >
                      Current Plan
                    </button>
                  ) : isFree ? (
                    <button
                      disabled
                      className="w-full py-3 px-4 bg-gray-100 text-gray-500 rounded-xl font-medium cursor-not-allowed"
                    >
                      Free Forever
                    </button>
                  ) : hasActiveSubscription ? (
                    <button
                      onClick={() => handleUpgrade(tier.id, tier.stripe_price_id)}
                      disabled={isProcessing || !tier.stripe_price_id}
                      className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 ${
                        tier.stripe_price_id
                          ? `bg-gradient-to-r ${getTierColor(tier.id)} text-white hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0`
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {isProcessing ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                          </svg>
                          Processing...
                        </span>
                      ) : tier.stripe_price_id ? (
                        'Switch Plan'
                      ) : (
                        'Coming Soon'
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={() => handleSubscribe(tier.id, tier.stripe_price_id)}
                      disabled={isProcessing || !tier.stripe_price_id}
                      className={`w-full py-3 px-4 rounded-xl font-medium transition-all duration-200 ${
                        tier.stripe_price_id
                          ? `bg-gradient-to-r ${getTierColor(tier.id)} text-white hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-50 disabled:hover:translate-y-0`
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      {isProcessing ? (
                        <span className="flex items-center justify-center">
                          <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" fill="none" viewBox="0 0 24 24">
                            <circle
                              className="opacity-25"
                              cx="12"
                              cy="12"
                              r="10"
                              stroke="currentColor"
                              strokeWidth="4"
                            ></circle>
                            <path
                              className="opacity-75"
                              fill="currentColor"
                              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                            ></path>
                          </svg>
                          Processing...
                        </span>
                      ) : tier.stripe_price_id ? (
                        'Get Started'
                      ) : (
                        'Coming Soon'
                      )}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        {/* FAQ Section */}
        <div className="max-w-3xl mx-auto">
          <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">Frequently Asked Questions</h2>
          <div className="space-y-4">
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="font-semibold text-gray-900 mb-2">Can I change my plan later?</h3>
              <p className="text-gray-600">
                Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately and billing is
                prorated.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-600">
                We accept all major credit cards (Visa, Mastercard, American Express) through our secure payment
                processor, Stripe.
              </p>
            </div>
            <div className="bg-white rounded-xl p-6 shadow-sm border">
              <h3 className="font-semibold text-gray-900 mb-2">Is there a money-back guarantee?</h3>
              <p className="text-gray-600">
                Yes! If you're not satisfied within the first 14 days, contact us for a full refund. No questions asked.
              </p>
            </div>
          </div>
        </div>

        {/* Billing History */}
        {hasActiveSubscription && billingHistory.length > 0 && (
          <div className="max-w-4xl mx-auto mt-12">
            <div className="bg-white rounded-xl shadow-sm border overflow-hidden">
              <div className="p-6 border-b">
                <h2 className="text-xl font-bold text-gray-900">Billing History</h2>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="text-left py-3 px-6 font-medium text-gray-600 text-sm">Date</th>
                      <th className="text-left py-3 px-6 font-medium text-gray-600 text-sm">Description</th>
                      <th className="text-left py-3 px-6 font-medium text-gray-600 text-sm">Amount</th>
                      <th className="text-left py-3 px-6 font-medium text-gray-600 text-sm">Status</th>
                      <th className="text-left py-3 px-6 font-medium text-gray-600 text-sm">Invoice</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-100">
                    {billingHistory.map(item => (
                      <tr key={item.id} className="hover:bg-gray-50">
                        <td className="py-4 px-6 text-sm text-gray-900">{formatDate(item.invoice_date)}</td>
                        <td className="py-4 px-6 text-sm text-gray-600">
                          {item.description || 'Subscription payment'}
                        </td>
                        <td className="py-4 px-6 text-sm font-medium text-gray-900">{formatCurrency(item.amount)}</td>
                        <td className="py-4 px-6">
                          <span
                            className={`inline-flex px-2.5 py-0.5 rounded-full text-xs font-medium ${
                              item.status === 'paid'
                                ? 'bg-green-100 text-green-700'
                                : item.status === 'failed'
                                  ? 'bg-red-100 text-red-700'
                                  : 'bg-yellow-100 text-yellow-700'
                            }`}
                          >
                            {item.status.charAt(0).toUpperCase() + item.status.slice(1)}
                          </span>
                        </td>
                        <td className="py-4 px-6">
                          {item.invoice_pdf_url && (
                            <a
                              href={item.invoice_pdf_url}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                            >
                              Download PDF
                            </a>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Footer */}
        <div className="text-center mt-12 text-gray-500 text-sm">
          <p>
            Questions? Contact us at{' '}
            <a href="mailto:support@example.com" className="text-blue-600 hover:underline">
              support@example.com
            </a>
          </p>
        </div>
      </div>
    </div>
  );
};

export default SubscriptionPage;
