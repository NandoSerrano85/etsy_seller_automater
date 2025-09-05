import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApi } from '../../hooks/useApi';

const OrdersTab = ({ isConnected, authUrl, orders, loading, error, onRefresh }) => {
  const [searchParams] = useSearchParams();
  const activeSubTab = searchParams.get('subtab') || 'all';
  const [expandedOrders, setExpandedOrders] = useState([]);
  // const [selectedOrders, setSelectedOrders] = useState([]);
  const [printLoading, setPrintLoading] = useState(false);
  const [printError, setPrintError] = useState(null);
  const [printMsg, setPrintMsg] = useState(null);
  const api = useApi();

  // Add send to print function
  const handleSendToPrint = async () => {
    if (orders.length === 0) {
      setPrintError('Please select at least one order to print');
      return;
    }

    try {
      setPrintLoading(true);
      setPrintError(null);
      setPrintMsg(null);

      const response = await api.get('/orders/create-print-files');
      console.log(response);
      if (response.success) {
        // Reset selection after successful print
        setSelectedOrders([]);
        // Show success message or handle downloads if needed
        setPrintMsg(response.message || 'Print files created successfully');
      } else {
        setPrintError(response.message || 'Failed to create print files');
      }
    } catch (error) {
      setPrintError(error.message || 'Error creating print files');
    } finally {
      setPrintLoading(false);
    }
  };

  // Add order selection handler
  // const handleOrderSelect = orderId => {
  //   setSelectedOrders(prev => (prev.includes(orderId) ? prev.filter(id => id !== orderId) : [...prev, orderId]));
  // };

  // Add print tab content
  const renderPrintTab = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold">Selected Orders for Print</h3>
            <button
              onClick={handleSendToPrint}
              disabled={orders.length === 0 || printLoading}
              className={`
                px-4 py-2 rounded-lg font-medium flex items-center space-x-2
                ${
                  orders.length === 0 || printLoading
                    ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                    : 'bg-lavender-500 text-white hover:bg-lavender-600'
                }
              `}
            >
              {printLoading ? (
                <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
              ) : (
                <>
                  <span>🖨️</span>
                  <span>Send to Print ({orders.length})</span>
                </>
              )}
            </button>
          </div>

          {printError && (
            <div className="bg-rose-50 border border-rose-200 rounded-lg p-4 mb-4">
              <p className="text-rose-700">{printError}</p>
            </div>
          )}

          {printMsg && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-4 mb-4">
              <p className="text-green-700">{printMsg}</p>
            </div>
          )}

          {/* Orders Table */}

          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-200">
                  {/* <th className="px-4 py-2 text-left">Select</th> */}
                  <th className="px-4 py-2 text-left">Order ID</th>
                  <th className="px-4 py-2 text-left">Customer</th>
                  <th className="px-4 py-2 text-left">Items</th>
                </tr>
              </thead>
              <tbody>
                {orders.map(order => (
                  <tr key={order.order_id} className="border-b border-gray-100">
                    {/* <td className="px-4 py-2">
                      <input
                        type="checkbox"
                        checked={selectedOrders.includes(order.order_id)}
                        // onChange={() => handleOrderSelect(order.order_id)}
                        className="rounded border-gray-300 text-lavender-600 focus:ring-lavender-500"
                      />
                    </td> */}
                    <td className="px-4 py-2">{order.order_id}</td>
                    <td className="px-4 py-2">{order.customer_name || 'N/A'}</td>
                    <td className="px-4 py-2">
                      {order.items?.reduce((total, item) => total + (item.quantity || 0), 0) || 0}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    );
  };

  const toggleOrderExpand = orderId => {
    setExpandedOrders(prev => (prev.includes(orderId) ? prev.filter(id => id !== orderId) : [...prev, orderId]));
  };
  const formatCurrency = (amount, divisor = 100) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
    }).format(amount / divisor);
  };

  if (!isConnected) {
    return (
      <div className="card p-8 text-center">
        <p className="text-lg text-gray-600 mb-6">Please connect your Etsy shop to view orders</p>
        <a href={authUrl} className="btn-primary">
          Connect Shop
        </a>
      </div>
    );
  }

  // if (loading) {
  //   return (
  //     <div className="flex items-center justify-center p-8">
  //       <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
  //       <span className="ml-2 text-sage-600">Loading orders...</span>
  //     </div>
  //   );
  // }

  if (error) {
    return (
      <div className="bg-rose-50 border border-rose-200 rounded-lg p-6">
        <p className="text-rose-700">{error}</p>
        <button onClick={onRefresh} className="mt-2 text-rose-600 hover:text-rose-700 text-sm underline">
          Try again
        </button>
      </div>
    );
  }
  // Modify the main return to include the print tab
  if (activeSubTab === 'print') {
    return renderPrintTab();
  }
  return (
    <div className="space-y-8">
      {/* Orders Summary Card */}
      <div className="card p-8">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 items-center">
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900">{(orders || []).length}</h3>
            <p className="text-gray-600">Total Orders</p>
          </div>
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900">
              {(orders || []).reduce(
                (sum, order) => sum + (order.items?.reduce((total, item) => total + (item.quantity || 0), 0) || 0),
                0
              )}
            </h3>
            <p className="text-gray-600">Total Items</p>
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
              {(orders || []).map(order => (
                <React.Fragment key={order.order_id}>
                  <tr className="hover:bg-gray-50">
                    <td className="px-2 py-4 text-center">
                      <button
                        onClick={() => toggleOrderExpand(order.order_id)}
                        className="focus:outline-none"
                        aria-label={expandedOrders.includes(order.order_id) ? 'Collapse' : 'Expand'}
                      >
                        {expandedOrders.includes(order.order_id) ? <span>&#9660;</span> : <span>&#9654;</span>}
                      </button>
                    </td>
                    <td className="px-6 py-4 font-medium text-gray-900">{order.order_id}</td>
                    <td className="px-6 py-4 text-gray-700">{order.customer_name || 'N/A'}</td>
                    <td className="px-6 py-4 text-gray-700">{order.shipping_method || 'N/A'}</td>
                    <td className="px-6 py-4 text-gray-700">{formatCurrency(order.shipping_cost || 0)}</td>
                    <td className="px-6 py-4 text-gray-700">
                      {new Date(order.order_date * 1000).toLocaleDateString()}
                    </td>
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
                              {(order.items || []).map((item, idx) => (
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
          {(orders || []).length === 0 && <div className="text-center py-8 text-gray-500">No active orders found</div>}
        </div>
      </div>
    </div>
  );
};

export default OrdersTab;
