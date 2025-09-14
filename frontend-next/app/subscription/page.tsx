'use client';

import { useState } from 'react';

interface Plan {
  id: string;
  name: string;
  price: string;
  priceId: string;
  features: string[];
  popular?: boolean;
}

export default function SubscriptionPage() {
  const [loading, setLoading] = useState<string>('');
  const [message, setMessage] = useState<string>('');

  const plans: Plan[] = [
    {
      id: 'free',
      name: 'Free',
      price: '$0',
      priceId: 'price_free',
      features: [
        'Up to 10 listings',
        'Basic templates',
        'Standard support',
        '1 mockup per month',
      ],
    },
    {
      id: 'pro',
      name: 'Pro',
      price: '$19',
      priceId: 'price_pro_monthly',
      popular: true,
      features: [
        'Unlimited listings',
        'Premium templates',
        'Priority support',
        'Unlimited mockups',
        'Advanced analytics',
        'Custom branding',
      ],
    },
    {
      id: 'team',
      name: 'Team',
      price: '$49',
      priceId: 'price_team_monthly',
      features: [
        'Everything in Pro',
        'Team collaboration',
        'API access',
        'White-label solution',
        'Dedicated account manager',
        'Custom integrations',
      ],
    },
  ];

  const handleSubscribe = async (priceId: string, planName: string) => {
    if (priceId === 'price_free') {
      setMessage('Free plan is already active!');
      return;
    }

    setLoading(priceId);
    setMessage('');

    try {
      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/billing/create-checkout-session`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ priceId }),
      });

      if (response.ok) {
        const result = await response.json();

        // Check if Stripe is available for redirect
        if (typeof window !== 'undefined' && (window as any).Stripe && process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY) {
          const stripe = (window as any).Stripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY);
          await stripe.redirectToCheckout({ sessionId: result.sessionId });
        } else {
          // Fallback: display session ID
          setMessage(`Checkout session created! Session ID: ${result.sessionId}`);
        }
      } else {
        setMessage(`Failed to create checkout session for ${planName}. Please try again.`);
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      setMessage('Error processing subscription. Please check your connection.');
    } finally {
      setLoading('');
    }
  };

  return (
    <div>
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">Choose Your Plan</h1>
        <p className="text-lg text-gray-600">
          Select the perfect plan for your Etsy automation needs
        </p>
      </div>

      {message && (
        <div className={`mb-6 p-4 rounded-md text-center ${
          message.includes('created') || message.includes('active')
            ? 'bg-green-50 text-green-700 border border-green-200'
            : 'bg-red-50 text-red-700 border border-red-200'
        }`}>
          {message}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-6xl mx-auto">
        {plans.map((plan) => (
          <div
            key={plan.id}
            className={`relative bg-white rounded-lg shadow-lg border-2 ${
              plan.popular ? 'border-primary' : 'border-gray-200'
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary text-white px-4 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}

            <div className="p-6">
              <div className="text-center mb-6">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                <div className="text-4xl font-bold text-gray-900 mb-1">
                  {plan.price}
                  {plan.price !== '$0' && <span className="text-lg text-gray-500">/month</span>}
                </div>
              </div>

              <ul className="space-y-3 mb-8">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center">
                    <svg
                      className="w-5 h-5 text-green-500 mr-3 flex-shrink-0"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M5 13l4 4L19 7"
                      />
                    </svg>
                    <span className="text-gray-600">{feature}</span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => handleSubscribe(plan.priceId, plan.name)}
                disabled={loading === plan.priceId}
                className={`w-full py-3 px-4 rounded-md font-medium transition-colors ${
                  plan.popular
                    ? 'bg-primary text-white hover:bg-opacity-90'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                } disabled:opacity-50`}
              >
                {loading === plan.priceId
                  ? 'Processing...'
                  : plan.id === 'free'
                  ? 'Current Plan'
                  : 'Subscribe'
                }
              </button>
            </div>
          </div>
        ))}
      </div>

      <div className="text-center mt-12 text-gray-500 text-sm">
        <p>All plans include a 14-day free trial. Cancel anytime.</p>
      </div>
    </div>
  );
}