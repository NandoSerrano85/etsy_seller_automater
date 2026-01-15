import React, { useEffect, useState } from 'react';
import { useSearchParams, Link } from 'react-router-dom';
import subscriptionService from '../../services/subscriptionService';

// Simple confetti effect using CSS
const ConfettiEffect = () => {
  const colors = ['#10b981', '#3b82f6', '#8b5cf6', '#f59e0b', '#ef4444', '#ec4899'];
  const confettiPieces = Array.from({ length: 50 }, (_, i) => ({
    id: i,
    left: Math.random() * 100,
    delay: Math.random() * 3,
    duration: 3 + Math.random() * 2,
    color: colors[Math.floor(Math.random() * colors.length)],
  }));

  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-50">
      <style>{`
        @keyframes confetti-fall {
          0% { transform: translateY(-100vh) rotate(0deg); opacity: 1; }
          100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
        }
      `}</style>
      {confettiPieces.map(piece => (
        <div
          key={piece.id}
          className="absolute w-3 h-3"
          style={{
            left: `${piece.left}%`,
            backgroundColor: piece.color,
            animation: `confetti-fall ${piece.duration}s ease-out ${piece.delay}s forwards`,
            borderRadius: Math.random() > 0.5 ? '50%' : '0',
          }}
        />
      ))}
    </div>
  );
};

const PaymentSuccessPage = () => {
  const [searchParams] = useSearchParams();
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showConfetti, setShowConfetti] = useState(true);

  const planId = searchParams.get('plan');

  useEffect(() => {
    // Stop confetti after 5 seconds
    const timer = setTimeout(() => setShowConfetti(false), 5000);
    return () => clearTimeout(timer);
  }, []);

  useEffect(() => {
    const fetchSubscription = async () => {
      try {
        const sub = await subscriptionService.getCurrentSubscription();
        setSubscription(sub);
      } catch (err) {
        console.error('Error fetching subscription:', err);
      } finally {
        setLoading(false);
      }
    };

    // Small delay to allow webhook to process
    const timer = setTimeout(fetchSubscription, 2000);
    return () => clearTimeout(timer);
  }, []);

  const formatDate = dateString => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const getTierColor = tierId => {
    const colors = {
      starter: 'from-blue-500 to-blue-600',
      pro: 'from-purple-500 to-purple-600',
      full: 'from-amber-500 to-orange-600',
    };
    return colors[tierId] || 'from-green-500 to-green-600';
  };

  const getTierName = tierId => {
    const names = {
      starter: 'Starter',
      pro: 'Pro',
      full: 'Full',
    };
    return names[tierId] || tierId;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center py-12 px-4">
      {showConfetti && <ConfettiEffect />}

      <div className="max-w-lg w-full">
        {/* Success Card */}
        <div className="bg-white rounded-3xl shadow-2xl overflow-hidden">
          {/* Header */}
          <div className="bg-gradient-to-r from-green-500 to-emerald-600 p-8 text-center">
            <div className="w-20 h-20 bg-white rounded-full flex items-center justify-center mx-auto mb-4 shadow-lg">
              <svg className="w-10 h-10 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={3} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h1 className="text-3xl font-bold text-white mb-2">Payment Successful!</h1>
            <p className="text-green-100">Welcome to the family</p>
          </div>

          {/* Content */}
          <div className="p-8">
            {loading ? (
              <div className="text-center py-8">
                <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-green-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading your subscription details...</p>
              </div>
            ) : (
              <>
                {/* Plan Info */}
                <div className="bg-gray-50 rounded-2xl p-6 mb-6">
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-600">Your Plan</span>
                    <span
                      className={`px-3 py-1 rounded-full text-white text-sm font-medium bg-gradient-to-r ${getTierColor(subscription?.tier || planId)}`}
                    >
                      {getTierName(subscription?.tier || planId)}
                    </span>
                  </div>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-gray-600">Status</span>
                    <span className="text-green-600 font-medium flex items-center">
                      <span className="w-2 h-2 bg-green-500 rounded-full mr-2 animate-pulse"></span>
                      Active
                    </span>
                  </div>
                  {subscription?.current_period_end && (
                    <div className="flex items-center justify-between">
                      <span className="text-gray-600">Next billing date</span>
                      <span className="text-gray-900 font-medium">{formatDate(subscription.current_period_end)}</span>
                    </div>
                  )}
                </div>

                {/* What's Next */}
                <div className="mb-8">
                  <h3 className="font-semibold text-gray-900 mb-4">What's next?</h3>
                  <ul className="space-y-3">
                    <li className="flex items-start">
                      <span className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium mr-3 flex-shrink-0">
                        1
                      </span>
                      <span className="text-gray-600">Your premium features are now unlocked and ready to use</span>
                    </li>
                    <li className="flex items-start">
                      <span className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium mr-3 flex-shrink-0">
                        2
                      </span>
                      <span className="text-gray-600">Check your email for a receipt and welcome guide</span>
                    </li>
                    <li className="flex items-start">
                      <span className="w-6 h-6 rounded-full bg-green-100 text-green-600 flex items-center justify-center text-sm font-medium mr-3 flex-shrink-0">
                        3
                      </span>
                      <span className="text-gray-600">Explore all your new tools and start creating</span>
                    </li>
                  </ul>
                </div>

                {/* Action Buttons */}
                <div className="space-y-3">
                  <Link
                    to="/"
                    className="block w-full py-3 px-6 bg-gradient-to-r from-green-500 to-emerald-600 text-white rounded-xl font-semibold text-center hover:shadow-lg transition-all duration-200"
                  >
                    Start Creating
                  </Link>
                  <Link
                    to="/subscription"
                    className="block w-full py-3 px-6 bg-gray-100 text-gray-700 rounded-xl font-semibold text-center hover:bg-gray-200 transition-colors"
                  >
                    View Subscription Details
                  </Link>
                </div>
              </>
            )}
          </div>
        </div>

        {/* Support Link */}
        <p className="text-center text-gray-600 mt-6 text-sm">
          Need help?{' '}
          <a href="mailto:support@example.com" className="text-green-600 hover:underline">
            Contact support
          </a>
        </p>
      </div>
    </div>
  );
};

export default PaymentSuccessPage;
