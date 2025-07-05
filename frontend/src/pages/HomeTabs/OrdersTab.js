import React from 'react';

const OrdersTab = ({
  accessToken,
  authUrl,
  ordersSummary,
  createPrintfile,
  creatingPrintfile,
  orders,
  expandedOrders,
  toggleOrderExpand,
  formatCurrency
}) => {
  if (!accessToken) {
    return (
      <div className="card p-8 text-center">
        <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view orders</p>
        <a href={authUrl} className="btn-primary">Connect Shop</a>
      </div>
    );
  }
  return (
    <div className="space-y-8">
      {/* Orders Summary Card */}
      <div className="card p-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 items-center">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900">{ordersSummary.totalOrders}</h3>
            <p className="text-gray-600">Total Orders</p>
          </div>
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900">{ordersSummary.totalItems}</h3>
            <p className="text-gray-600">Total Items Sold</p>
          </div>
          <div className="text-center">
            <button
              onClick={createPrintfile}
              disabled={creatingPrintfile}
              className={`px-6 py-3 rounded-lg font-medium transition-colors ${
                creatingPrintfile 
                  ? 'bg-gray-400 text-white cursor-not-allowed' 
                  : 'bg-blue-500 text-white hover:bg-blue-600'
              }`}
            >
              {creatingPrintfile ? (
                <div className="flex items-center justify-center space-x-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  <span>Creating...</span>
                </div>
              ) : (
                'Create Printfile'
              )}
            </button>
          </div>
        </div>
      </div>
      {/* Orders Table */}
      <div className="card p-6">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Active Orders</h2>
        <div className="overflow-x-auto rounded-lg shadow">
          <table className="w-full bg-white">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-4 text-left font-semibold text-gray-700"></th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Order ID</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Customer Name</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Shipping Method</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Shipping Cost</th>
                <th className="px-6 py-4 text-left font-semibold text-gray-700">Order Date</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {orders.map((order) => (
                <React.Fragment key={order.order_id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-2 py-4 text-center">
                      <button
                        onClick={() => toggleOrderExpand(order.order_id)}
                        className="focus:outline-none"
                        aria-label={expandedOrders.includes(order.order_id) ? 'Collapse' : 'Expand'}
                      >
                        {expandedOrders.includes(order.order_id) ? (
                          <span>&#9660;</span>
                        ) : (
                          <span>&#9654;</span>
                        )}
                      </button>
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900">{order.order_id}</td>
                    <td className="px-6 py-4 text-gray-700">{order.customer_name || 'N/A'}</td>
                    <td className="px-6 py-4 text-gray-700">{order.shipping_method || 'N/A'}</td>
                    <td className="px-6 py-4 text-gray-700">{formatCurrency(order.shipping_cost || 0)}</td>
                    <td className="px-6 py-4 text-gray-700">{new Date(order.order_date * 1000).toLocaleDateString()}</td>
                  </tr>
                  {/* Transactions Dropdown */}
                  {expandedOrders.includes(order.order_id) && (
                    <tr>
                      <td colSpan={6} className="bg-gray-50 px-6 py-4">
                        <div className="overflow-x-auto">
                          <table className="w-full">
                            <thead>
                              <tr>
                                <th className="px-4 py-2 text-left font-semibold text-gray-700">Item Name</th>
                                <th className="px-4 py-2 text-left font-semibold text-gray-700">Quantity</th>
                                <th className="px-4 py-2 text-left font-semibold text-gray-700">Price</th>
                              </tr>
                            </thead>
                            <tbody>
                              {order.items.map((item, idx) => (
                                <tr key={idx}>
                                  <td className="px-4 py-2 text-gray-700">{item.title || 'N/A'}</td>
                                  <td className="px-4 py-2 text-gray-700">{item.quantity || 0}</td>
                                  <td className="px-4 py-2 text-gray-700">{formatCurrency(item.price || 0)}</td>
                                </tr>
                              ))}
                            </tbody>
                          </table>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
          {orders.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              No active orders found
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default OrdersTab; 