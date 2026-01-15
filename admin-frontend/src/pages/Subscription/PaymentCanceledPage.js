import React from 'react';
import { useSearchParams, Link } from 'react-router-dom';

const PaymentCanceledPage = () => {
  const [searchParams] = useSearchParams();
  const planId = searchParams.get('plan');

  const getTierName = tierId => {
    const names = {
      starter: 'Starter',
      pro: 'Pro',
      full: 'Full',
    };
    return names[tierId] || tierId;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-gray-100 flex items-center justify-center py-12 px-4">
      <div className="max-w-lg w-full">
        {/* Canceled Card */}
        <div className="bg-white rounded-3xl shadow-xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-gray-600 to-gray-700 p-8 text-center">
            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
              <svg className="w-10 h-10 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Checkout Canceled</h1>
            <p className="text-gray-300">No worries, you weren't charged</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {/* Info Box */}
            <div className="bg-blue-50 border border-blue-200 rounded-2xl p-5 mb-6">
              <div className="flex">
                <svg className="w-6 h-6 text-blue-500 mr-3 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                    clipRule="evenodd"
                  />
                </svg>
                <div>
                  <p className="font-medium text-blue-900 mb-1">Your cart is saved</p>
                  <p className="text-sm text-blue-700">
                    {planId ? (
                      <>The {getTierName(planId)} plan is still available whenever you're ready.</>
                    ) : (
                      <>Your selected plan is still available whenever you're ready.</>
                    )}
                  </p>
                </div>
              </div>
            </div>

            {/* Reasons to Subscribe */}
            <div className="mb-8">
              <h3 className="font-semibold text-gray-900 mb-4">Still thinking about it?</h3>
              <ul className="space-y-3">
                <li className="flex items-start text-sm">
                  <svg
                    className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-600">14-day money-back guarantee - try risk-free</span>
                </li>
                <li className="flex items-start text-sm">
                  <svg
                    className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-600">Cancel anytime with no questions asked</span>
                </li>
                <li className="flex items-start text-sm">
                  <svg
                    className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-600">Instant access to all premium features</span>
                </li>
                <li className="flex items-start text-sm">
                  <svg
                    className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <span className="text-gray-600">Priority support from our team</span>
                </li>
              </ul>
            </div>

            {/* Action Buttons */}
            <div className="space-y-3">
              <Link
                to="/subscription"
                className="block w-full py-3 px-6 bg-gradient-to-r from-blue-500 to-blue-600 text-white rounded-xl font-semibold text-center hover:shadow-lg transition-all duration-200"
              >
                View Plans Again
              </Link>
              <Link
                to="/"
                className="block w-full py-3 px-6 bg-gray-100 text-gray-700 rounded-xl font-semibold text-center hover:bg-gray-200 transition-colors"
              >
                Return to Dashboard
              </Link>
            </div>
          </div>
        </div>

        {/* Help Link */}
        <div className="text-center mt-6">
          <p className="text-gray-600 text-sm mb-2">Have questions about our plans?</p>
          <a href="mailto:support@example.com" className="text-blue-600 hover:underline text-sm font-medium">
            Talk to our team
          </a>
        </div>
      </div>
    </div>
  );
};

export default PaymentCanceledPage;
