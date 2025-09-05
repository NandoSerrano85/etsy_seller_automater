import React from 'react';

const OverviewTab = ({ user, isConnected, designs, topSellers, authUrl }) => {
  return (
    <div className="space-y-6 sm:space-y-8">
      <div className="card p-6 sm:p-8 text-center">
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900 mb-4">Welcome to Your Dashboard</h2>
        {user && (
          <p className="text-base sm:text-lg text-gray-600 mb-4">
            Hello, <span className="font-semibold text-blue-600">{user.email}</span>!
          </p>
        )}
        <p className="text-base sm:text-lg text-gray-600 mb-6 sm:mb-8">
          Get insights into your shop performance, manage your designs, and use powerful tools to grow your business.
        </p>
        {!isConnected ? (
          <div className="bg-blue-50 border-l-4 border-blue-400 p-4 sm:p-6 rounded-lg">
            <p className="text-blue-700 mb-4 text-sm sm:text-base">Connect your Etsy shop to get started</p>
            <a href={authUrl} className="btn-primary">
              Connect Shop
            </a>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 sm:gap-6 mt-6 sm:mt-8">
            <div className="bg-gradient-to-r from-blue-500 to-purple-600 text-white p-4 sm:p-6 rounded-xl text-center">
              <h3 className="text-base sm:text-lg font-semibold mb-2">Total Designs</h3>
              <p className="text-2xl sm:text-3xl font-bold">{designs.length}</p>
            </div>
            <div className="bg-gradient-to-r from-green-500 to-teal-600 text-white p-4 sm:p-6 rounded-xl text-center">
              <h3 className="text-base sm:text-lg font-semibold mb-2">Top Seller</h3>
              <p className="text-sm sm:text-lg font-medium">
                {topSellers.length > 0 ? topSellers[0]?.title?.substring(0, 20) + '...' : 'N/A'}
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default OverviewTab;
