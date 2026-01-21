import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import { loadStripe } from '@stripe/stripe-js';
import subscriptionService from '../../services/subscriptionService';

const stripePromise = loadStripe(process.env.REACT_APP_STRIPE_PUBLISHABLE_KEY);

// Format tier features for display
const formatTierFeatures = tier => {
  const features = tier.features || {};
  const limits = tier.limits || {};
  const displayFeatures = [];

  // Mockup Generator features
  if (features.mockup_generator) {
    const mockupLimit = limits.monthly_mockups;
    displayFeatures.push(mockupLimit === -1 ? 'Unlimited mockups/month' : `${mockupLimit} mockups/month`);

    const batchLimit = limits.mockups_per_batch;
    if (batchLimit === -1) {
      displayFeatures.push('Unlimited batch creation');
    } else if (batchLimit === 1) {
      displayFeatures.push('1 mockup at a time');
    } else {
      displayFeatures.push(`${batchLimit} mockups per batch`);
    }

    const templateLimit = limits.templates;
    displayFeatures.push(
      templateLimit === -1 ? 'Unlimited templates' : `${templateLimit} template${templateLimit > 1 ? 's' : ''}`
    );
  }

  // Integrations
  if (features.etsy_integration) displayFeatures.push('Etsy Integration');
  if (features.shopify_integration) displayFeatures.push('Shopify Integration');
  if (features.craftflow_commerce) displayFeatures.push('CraftFlow Commerce');

  // Additional features
  if (features.file_cleaner) displayFeatures.push('File Cleaner');
  if (features.auto_naming) displayFeatures.push('Auto Naming');
  if (features.batch_uploads) displayFeatures.push('Batch Uploads');
  if (features.advanced_resizing) displayFeatures.push('Advanced Resizing');
  if (features.print_file_generator) displayFeatures.push('Print File Generator');
  if (features.csv_export) displayFeatures.push('CSV Export');
  if (features.multi_shop_support) displayFeatures.push('Multi-Shop Support');
  if (features.priority_support) displayFeatures.push('Priority Support');

  return displayFeatures;
};

const CheckoutPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [selectedTier, setSelectedTier] = useState(null);
  const [loading, setLoading] = useState(true);
  const [processing, setProcessing] = useState(false);
  const [error, setError] = useState(null);
  const [agreedToTerms, setAgreedToTerms] = useState(false);

  const planId = searchParams.get('plan');

  useEffect(() => {
    const fetchTierData = async () => {
      if (!planId) {
        navigate('/subscription');
        return;
      }

      try {
        setLoading(true);
        const { tiers } = await subscriptionService.getSubscriptionTiers();
        const tier = tiers.find(t => t.id === planId);

        if (!tier || tier.id === 'free') {
          navigate('/subscription');
          return;
        }

        setSelectedTier(tier);
      } catch (err) {
        console.error('Error fetching tier data:', err);
        setError('Failed to load plan details. Please try again.');
      } finally {
        setLoading(false);
      }
    };

    fetchTierData();
  }, [planId, navigate]);

  const handleCheckout = async () => {
    if (!agreedToTerms) {
      setError('Please agree to the terms and conditions to continue.');
      return;
    }

    if (!selectedTier?.stripe_price_id) {
      setError('This plan is not available for purchase yet.');
      return;
    }

    try {
      setProcessing(true);
      setError(null);

      const stripe = await stripePromise;

      const { session_id } = await subscriptionService.createCheckoutSession(
        selectedTier.stripe_price_id,
        `${window.location.origin}/subscription/success?plan=${selectedTier.id}`,
        `${window.location.origin}/subscription/canceled?plan=${selectedTier.id}`
      );

      const result = await stripe.redirectToCheckout({ sessionId: session_id });

      if (result.error) {
        setError(result.error.message);
      }
    } catch (err) {
      console.error('Error during checkout:', err);
      setError('Failed to start checkout. Please try again.');
    } finally {
      setProcessing(false);
    }
  };

  const formatCurrency = amount => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount);
  };

  const getTierColor = tierId => {
    const colors = {
      starter: 'from-blue-500 to-blue-600',
      pro: 'from-purple-500 to-purple-600',
      full: 'from-amber-500 to-orange-600',
    };
    return colors[tierId] || 'from-gray-500 to-gray-600';
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading checkout...</p>
        </div>
      </div>
    );
  }

  if (!selectedTier) {
    return null;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 py-12">
      <div className="max-w-4xl mx-auto px-4">
        {/* Back Link */}
        <Link
          to="/subscription"
          className="inline-flex items-center text-gray-600 hover:text-gray-900 mb-8 transition-colors"
        >
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to plans
        </Link>

        <div className="grid md:grid-cols-2 gap-8">
          {/* Order Summary */}
          <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
            <div className={`p-6 bg-gradient-to-br ${getTierColor(selectedTier.id)}`}>
              <h2 className="text-2xl font-bold text-white mb-1">Order Summary</h2>
              <p className="text-white/80">Review your subscription</p>
            </div>

            <div className="p-6">
              {/* Plan Details */}
              <div className="flex items-center justify-between mb-6 pb-6 border-b">
                <div>
                  <h3 className="text-xl font-bold text-gray-900">{selectedTier.name} Plan</h3>
                  <p className="text-gray-500">Monthly subscription</p>
                </div>
                <div className="text-right">
                  <p className="text-2xl font-bold text-gray-900">{formatCurrency(selectedTier.price)}</p>
                  <p className="text-gray-500 text-sm">/month</p>
                </div>
              </div>

              {/* Features List */}
              <div className="mb-6">
                <h4 className="font-semibold text-gray-900 mb-3">What's included:</h4>
                <ul className="space-y-2">
                  {formatTierFeatures(selectedTier).map((feature, index) => (
                    <li key={index} className="flex items-center text-sm text-gray-600">
                      <svg
                        className="w-4 h-4 text-green-500 mr-2 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <span>{feature}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Total */}
              <div className="bg-gray-50 -mx-6 -mb-6 p-6">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-gray-600">Subtotal</span>
                  <span className="text-gray-900">{formatCurrency(selectedTier.price)}</span>
                </div>
                <div className="flex items-center justify-between mb-4 pb-4 border-b border-gray-200">
                  <span className="text-gray-600">Tax</span>
                  <span className="text-gray-500 text-sm">Calculated at checkout</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-lg font-bold text-gray-900">Total due today</span>
                  <span className="text-2xl font-bold text-gray-900">{formatCurrency(selectedTier.price)}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Payment Section */}
          <div className="bg-white rounded-2xl shadow-lg p-6">
            <h2 className="text-2xl font-bold text-gray-900 mb-6">Complete Your Purchase</h2>

            {/* Security Badges */}
            <div className="flex items-center gap-4 mb-6 pb-6 border-b">
              <div className="flex items-center text-sm text-gray-500">
                <svg className="w-5 h-5 mr-1 text-green-500" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                    clipRule="evenodd"
                  />
                </svg>
                SSL Secured
              </div>
              <div className="flex items-center text-sm text-gray-500">
                <svg className="w-5 h-5 mr-1 text-blue-500" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z" />
                  <path
                    fillRule="evenodd"
                    d="M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9zM4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1zm5-1a1 1 0 100 2h1a1 1 0 100-2H9z"
                    clipRule="evenodd"
                  />
                </svg>
                Powered by Stripe
              </div>
            </div>

            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 mb-6">
              <div className="flex">
                <svg
                  className="w-5 h-5 text-blue-500 mr-3 flex-shrink-0 mt-0.5"
                  fill="currentColor"
                  viewBox="0 0 20 20"
                >
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
                <div className="text-sm">
                  <p className="font-medium text-blue-900">Secure payment</p>
                  <p className="text-blue-700">
                    You'll be redirected to Stripe's secure checkout to complete your payment. Your card details are
                    never stored on our servers.
                  </p>
                </div>
              </div>
            </div>

            {/* Terms Checkbox */}
            <div className="mb-6">
              <label className="flex items-start cursor-pointer">
                <input
                  type="checkbox"
                  checked={agreedToTerms}
                  onChange={e => setAgreedToTerms(e.target.checked)}
                  className="mt-1 h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded"
                />
                <span className="ml-3 text-sm text-gray-600">
                  I agree to the{' '}
                  <a href="/terms" className="text-blue-600 hover:underline">
                    Terms of Service
                  </a>{' '}
                  and{' '}
                  <a href="/privacy" className="text-blue-600 hover:underline">
                    Privacy Policy
                  </a>
                  . I understand that my subscription will auto-renew monthly until canceled.
                </span>
              </label>
            </div>

            {/* Error Message */}
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-xl mb-6 flex items-center">
                <svg className="w-5 h-5 mr-2 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                    clipRule="evenodd"
                  />
                </svg>
                {error}
              </div>
            )}

            {/* Checkout Button */}
            <button
              onClick={handleCheckout}
              disabled={processing || !agreedToTerms}
              className={`w-full py-4 px-6 rounded-xl font-semibold text-lg transition-all duration-200 ${
                agreedToTerms
                  ? `bg-gradient-to-r ${getTierColor(selectedTier.id)} text-white hover:shadow-lg hover:-translate-y-0.5 disabled:opacity-70`
                  : 'bg-gray-200 text-gray-500 cursor-not-allowed'
              }`}
            >
              {processing ? (
                <span className="flex items-center justify-center">
                  <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
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
              ) : (
                `Subscribe for ${formatCurrency(selectedTier.price)}/month`
              )}
            </button>

            {/* Guarantee */}
            <p className="text-center text-sm text-gray-500 mt-4">
              <svg className="w-4 h-4 inline mr-1" fill="currentColor" viewBox="0 0 20 20">
                <path
                  fillRule="evenodd"
                  d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                  clipRule="evenodd"
                />
              </svg>
              14-day money-back guarantee. Cancel anytime.
            </p>
          </div>
        </div>

        {/* Trust Indicators */}
        <div className="mt-12 text-center">
          <p className="text-gray-500 text-sm mb-4">Trusted by thousands of sellers worldwide</p>
          <div className="flex items-center justify-center gap-8 text-gray-400">
            <div className="flex items-center">
              <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5" />
              </svg>
              <span className="text-sm">256-bit encryption</span>
            </div>
            <div className="flex items-center">
              <svg className="w-6 h-6 mr-2" fill="currentColor" viewBox="0 0 24 24">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              </svg>
              <span className="text-sm">PCI compliant</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CheckoutPage;
