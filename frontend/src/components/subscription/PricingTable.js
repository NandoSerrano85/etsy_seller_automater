import React from 'react';
import { useSubscription } from '../../hooks/useSubscription';
import TierBadge from './TierBadge';

const PricingTable = ({ className = '', onSelectPlan = null, highlightCurrent = true }) => {
  const { getAllTierConfigs, currentTier, SUBSCRIPTION_TIERS } = useSubscription();

  const tiers = getAllTierConfigs();

  const handleSelectPlan = tierKey => {
    if (onSelectPlan) {
      onSelectPlan(tierKey);
    } else {
      // Default behavior - log for now
      console.log(`Selected plan: ${tierKey}`);
    }
  };

  const getFeatureIcon = hasFeature => {
    return hasFeature ? <span className="text-green-500">✓</span> : <span className="text-gray-300">✕</span>;
  };

  return (
    <div className={`bg-white ${className}`}>
      <div className="text-center mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-4">Choose Your Plan</h2>
        <p className="text-lg text-gray-600">Scale your Etsy business with the right tools for your needs</p>
      </div>

      <div className="grid md:grid-cols-3 gap-8">
        {Object.entries(tiers).map(([tierKey, config]) => {
          const isCurrent = highlightCurrent && tierKey === currentTier;
          const isPopular = tierKey === SUBSCRIPTION_TIERS.PRO;

          return (
            <div
              key={tierKey}
              className={`
                relative rounded-2xl border-2 p-8
                ${
                  isCurrent
                    ? 'border-blue-500 bg-blue-50'
                    : isPopular
                      ? 'border-purple-500 bg-gradient-to-b from-purple-50 to-white'
                      : 'border-gray-200 bg-white'
                }
                transition-all duration-300 hover:shadow-lg
              `}
            >
              {isPopular && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <span className="bg-purple-600 text-white px-4 py-1 rounded-full text-sm font-medium">
                    Most Popular
                  </span>
                </div>
              )}

              {isCurrent && (
                <div className="absolute -top-4 left-1/2 transform -translate-x-1/2">
                  <TierBadge tier={tierKey} />
                </div>
              )}

              <div className="text-center mb-8">
                <h3 className="text-2xl font-bold text-gray-900 mb-2">{config.name}</h3>
                <p className="text-gray-600 mb-4">{config.description}</p>
                <div className="mb-4">
                  <span className="text-4xl font-bold text-gray-900">${config.price}</span>
                  {config.price > 0 && <span className="text-gray-600">/month</span>}
                </div>
              </div>

              <div className="space-y-4 mb-8">
                <h4 className="font-semibold text-gray-900 border-b pb-2">Features Included:</h4>

                {/* Core Features */}
                <div className="space-y-3">
                  <div className="flex items-center space-x-3">
                    {getFeatureIcon(config.features.etsy_dashboard)}
                    <span className="text-sm">Etsy Dashboard & Analytics</span>
                  </div>

                  <div className="flex items-center space-x-3">
                    {getFeatureIcon(config.features.mockup_generator)}
                    <span className="text-sm">
                      Mockup Generator
                      {config.limits.mockupsPerMonth !== Infinity && (
                        <span className="text-gray-500"> ({config.limits.mockupsPerMonth} per month)</span>
                      )}
                      {config.features.unlimited_mockups && (
                        <span className="text-green-600 font-medium"> (Unlimited)</span>
                      )}
                    </span>
                  </div>

                  <div className="flex items-center space-x-3">
                    {getFeatureIcon(config.features.file_cleaner)}
                    <span className="text-sm">File Cleaner (remove backgrounds)</span>
                  </div>

                  {/* Pro Features */}
                  {tierKey !== SUBSCRIPTION_TIERS.FREE && (
                    <>
                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.listing_templates)}
                        <span className="text-sm">Listing Templates & Auto-naming</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.file_resizing)}
                        <span className="text-sm">File Resizing & Bulk Operations</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.batch_uploads)}
                        <span className="text-sm">Batch Product Uploads</span>
                      </div>
                    </>
                  )}

                  {/* Print Pro Features */}
                  {tierKey === SUBSCRIPTION_TIERS.PRINT_PRO && (
                    <>
                      <div className="border-t pt-3 mt-3">
                        <div className="text-xs font-semibold text-purple-600 mb-2 uppercase tracking-wide">
                          Print Shop Pro Features
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.print_file_generator)}
                        <span className="text-sm">Print File Generator (batch orders)</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.advanced_resizing)}
                        <span className="text-sm">Advanced Resizing (DTF/Sublimation/Vinyl)</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.csv_export)}
                        <span className="text-sm">CSV/Excel Export</span>
                      </div>

                      <div className="flex items-center space-x-3">
                        {getFeatureIcon(config.features.multi_shop_support)}
                        <span className="text-sm">Multi-shop Support</span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              <button
                onClick={() => handleSelectPlan(tierKey)}
                disabled={isCurrent}
                className={`
                  w-full py-3 px-6 rounded-lg font-semibold transition-all duration-300
                  ${
                    isCurrent
                      ? 'bg-gray-100 text-gray-500 cursor-not-allowed'
                      : isPopular
                        ? 'bg-purple-600 hover:bg-purple-700 text-white'
                        : 'bg-gray-900 hover:bg-gray-800 text-white'
                  }
                `}
              >
                {isCurrent ? 'Current Plan' : `Choose ${config.name}`}
              </button>
            </div>
          );
        })}
      </div>

      <div className="mt-12 text-center">
        <p className="text-gray-600">All plans include 30-day money-back guarantee • Cancel anytime • No setup fees</p>
      </div>
    </div>
  );
};

export default PricingTable;
