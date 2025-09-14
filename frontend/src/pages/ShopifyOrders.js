import React, { useState, useEffect } from 'react';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import { useNavigate } from 'react-router-dom';
import {
  ShoppingBagIcon,
  MagnifyingGlassIcon,
  FunnelIcon,
  EyeIcon,
  UserIcon,
  CurrencyDollarIcon,
  CalendarDaysIcon,
  TruckIcon,
  ExclamationTriangleIcon,
  ClockIcon,
  CheckCircleIcon,
  LinkIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';

const ShopifyOrders = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [fulfillmentFilter, setFulfillmentFilter] = useState('all');
  const [selectedOrder, setSelectedOrder] = useState(null);
  const [storeConnected, setStoreConnected] = useState(true);

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async (showRefreshing = false) => {
    try {
      if (showRefreshing) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      const response = await fetch('/api/shopify/orders', {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        if (response.status === 404) {
          // No store connected
          setStoreConnected(false);
          return;
        }
        throw new Error('Failed to load orders');
      }

      const data = await response.json();
      setOrders(data.orders || []);
      setStoreConnected(true);
    } catch (error) {
      console.error('Error loading orders:', error);
      if (error.message.includes('store')) {
        setStoreConnected(false);
      } else {
        addNotification('Failed to load orders', 'error');
      }
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const refreshOrders = () => {
    loadOrders(true);
  };

  const getOrderById = async orderId => {
    try {
      const response = await fetch(`/api/shopify/orders/${orderId}`, {
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error('Failed to load order details');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error loading order details:', error);
      addNotification('Failed to load order details', 'error');
      return null;
    }
  };

  const openInShopify = order => {
    // Construct Shopify admin URL for the order
    const shopDomain = 'your-shop'; // Would need to get this from store info
    window.open(`https://${shopDomain}.myshopify.com/admin/orders/${order.id}`, '_blank');
  };

  // Filter orders based on search and status
  const filteredOrders = orders.filter(order => {
    const matchesSearch =
      order.name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customer?.first_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customer?.last_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customer?.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.id?.toString().includes(searchTerm);

    const matchesStatus =
      statusFilter === 'all' ||
      (statusFilter === 'paid' && order.financial_status === 'paid') ||
      (statusFilter === 'pending' && order.financial_status === 'pending') ||
      (statusFilter === 'refunded' && order.financial_status === 'refunded') ||
      order.financial_status === statusFilter;

    const matchesFulfillment =
      fulfillmentFilter === 'all' ||
      (fulfillmentFilter === 'fulfilled' && order.fulfillment_status === 'fulfilled') ||
      (fulfillmentFilter === 'unfulfilled' &&
        (order.fulfillment_status === null || order.fulfillment_status === 'unfulfilled')) ||
      order.fulfillment_status === fulfillmentFilter;

    return matchesSearch && matchesStatus && matchesFulfillment;
  });

  const getStatusBadge = (status, type = 'financial') => {
    const baseClasses = 'inline-flex px-2 py-1 text-xs font-semibold rounded-full';

    if (type === 'financial') {
      switch (status) {
        case 'paid':
          return `${baseClasses} bg-green-100 text-green-800`;
        case 'pending':
          return `${baseClasses} bg-yellow-100 text-yellow-800`;
        case 'refunded':
          return `${baseClasses} bg-red-100 text-red-800`;
        case 'partially_refunded':
          return `${baseClasses} bg-orange-100 text-orange-800`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`;
      }
    } else {
      switch (status) {
        case 'fulfilled':
          return `${baseClasses} bg-green-100 text-green-800`;
        case 'partial':
          return `${baseClasses} bg-yellow-100 text-yellow-800`;
        case 'unfulfilled':
        case null:
          return `${baseClasses} bg-gray-100 text-gray-800`;
        default:
          return `${baseClasses} bg-gray-100 text-gray-800`;
      }
    }
  };

  if (!storeConnected) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="bg-white rounded-lg shadow-lg p-8 max-w-md w-full text-center">
          <ExclamationTriangleIcon className="w-16 h-16 text-amber-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-gray-900 mb-2">No Store Connected</h2>
          <p className="text-gray-600 mb-6">Please connect your Shopify store to view and manage orders.</p>
          <button
            onClick={() => navigate('/shopify/connect')}
            className="bg-sage-600 text-white px-6 py-2 rounded-md hover:bg-sage-700"
          >
            Connect Shopify Store
          </button>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading orders...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Shopify Orders</h1>
            <p className="text-gray-600">Track and manage your store orders</p>
          </div>
          <button
            onClick={refreshOrders}
            disabled={refreshing}
            className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700 disabled:opacity-50"
          >
            <ArrowPathIcon className={`w-4 h-4 mr-2 ${refreshing ? 'animate-spin' : ''}`} />
            {refreshing ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>

        {/* Filters and Search */}
        <div className="bg-white rounded-lg shadow-lg p-6 mb-6">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between space-y-3 sm:space-y-0">
            {/* Search */}
            <div className="relative flex-1 max-w-md">
              <MagnifyingGlassIcon className="w-5 h-5 text-gray-400 absolute left-3 top-1/2 transform -translate-y-1/2" />
              <input
                type="text"
                placeholder="Search orders, customers..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 border border-gray-300 rounded-md w-full focus:ring-sage-500 focus:border-sage-500"
              />
            </div>

            <div className="flex items-center space-x-3">
              {/* Financial Status Filter */}
              <select
                value={statusFilter}
                onChange={e => setStatusFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-sage-500 focus:border-sage-500"
              >
                <option value="all">All Payments</option>
                <option value="paid">Paid</option>
                <option value="pending">Pending</option>
                <option value="refunded">Refunded</option>
                <option value="partially_refunded">Partially Refunded</option>
              </select>

              {/* Fulfillment Status Filter */}
              <select
                value={fulfillmentFilter}
                onChange={e => setFulfillmentFilter(e.target.value)}
                className="border border-gray-300 rounded-md px-3 py-2 focus:ring-sage-500 focus:border-sage-500"
              >
                <option value="all">All Fulfillment</option>
                <option value="fulfilled">Fulfilled</option>
                <option value="unfulfilled">Unfulfilled</option>
                <option value="partial">Partially Fulfilled</option>
              </select>
            </div>
          </div>

          {/* Results Count */}
          <div className="mt-4 text-sm text-gray-600">
            Showing {filteredOrders.length} of {orders.length} orders
          </div>
        </div>

        {/* Orders Table */}
        {filteredOrders.length === 0 ? (
          <div className="bg-white rounded-lg shadow-lg p-12 text-center">
            <ShoppingBagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">
              {orders.length === 0 ? 'No orders found' : 'No orders match your filters'}
            </h3>
            <p className="text-gray-600">
              {orders.length === 0
                ? 'Orders will appear here when customers make purchases from your store.'
                : 'Try adjusting your search criteria or filters.'}
            </p>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-lg overflow-hidden">
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Order
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Date
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Payment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Fulfillment
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Total
                    </th>
                    <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {filteredOrders.map(order => (
                    <tr key={order.id} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">
                            {order.name || `#${order.order_number || order.id}`}
                          </div>
                          <div className="text-sm text-gray-500">ID: {order.id}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <UserIcon className="w-5 h-5 text-gray-400 mr-2" />
                          <div>
                            <div className="text-sm font-medium text-gray-900">
                              {order.customer
                                ? `${order.customer.first_name || ''} ${order.customer.last_name || ''}`.trim() ||
                                  'Guest'
                                : 'Guest'}
                            </div>
                            <div className="text-sm text-gray-500">{order.customer?.email || 'No email'}</div>
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <CalendarDaysIcon className="w-4 h-4 text-gray-400 mr-2" />
                          <div className="text-sm text-gray-900">{new Date(order.created_at).toLocaleDateString()}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getStatusBadge(order.financial_status, 'financial')}>
                          {order.financial_status || 'unknown'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={getStatusBadge(order.fulfillment_status, 'fulfillment')}>
                          {order.fulfillment_status || 'unfulfilled'}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="flex items-center">
                          <CurrencyDollarIcon className="w-4 h-4 text-gray-400 mr-1" />
                          <span className="text-sm font-medium text-gray-900">
                            {order.total_price ? `$${parseFloat(order.total_price).toFixed(2)}` : 'N/A'}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <button
                            onClick={() => setSelectedOrder(order)}
                            className="text-blue-600 hover:text-blue-900"
                            title="View Details"
                          >
                            <EyeIcon className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => openInShopify(order)}
                            className="text-green-600 hover:text-green-900"
                            title="Open in Shopify"
                          >
                            <LinkIcon className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Order Detail Modal */}
        {selectedOrder && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl max-h-full overflow-auto">
              <div className="flex items-center justify-between p-6 border-b">
                <h3 className="text-lg font-semibold">
                  Order {selectedOrder.name || `#${selectedOrder.order_number || selectedOrder.id}`}
                </h3>
                <button onClick={() => setSelectedOrder(null)} className="text-gray-400 hover:text-gray-600">
                  ×
                </button>
              </div>

              <div className="p-6 space-y-6">
                {/* Order Summary */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Order Information</h4>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-600">Order ID:</span>
                        <span className="font-medium">{selectedOrder.id}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Date:</span>
                        <span className="font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Payment Status:</span>
                        <span className={getStatusBadge(selectedOrder.financial_status, 'financial')}>
                          {selectedOrder.financial_status || 'unknown'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Fulfillment:</span>
                        <span className={getStatusBadge(selectedOrder.fulfillment_status, 'fulfillment')}>
                          {selectedOrder.fulfillment_status || 'unfulfilled'}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-600">Total:</span>
                        <span className="font-medium text-lg">
                          ${selectedOrder.total_price ? parseFloat(selectedOrder.total_price).toFixed(2) : '0.00'}
                        </span>
                      </div>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Customer Information</h4>
                    {selectedOrder.customer ? (
                      <div className="space-y-2 text-sm">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Name:</span>
                          <span className="font-medium">
                            {`${selectedOrder.customer.first_name || ''} ${selectedOrder.customer.last_name || ''}`.trim() ||
                              'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Email:</span>
                          <span className="font-medium">{selectedOrder.customer.email || 'N/A'}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Phone:</span>
                          <span className="font-medium">{selectedOrder.customer.phone || 'N/A'}</span>
                        </div>
                      </div>
                    ) : (
                      <p className="text-sm text-gray-600">Guest customer</p>
                    )}
                  </div>
                </div>

                {/* Line Items */}
                {selectedOrder.line_items && selectedOrder.line_items.length > 0 && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Order Items</h4>
                    <div className="border rounded-lg overflow-hidden">
                      <table className="min-w-full divide-y divide-gray-200">
                        <thead className="bg-gray-50">
                          <tr>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">
                              Quantity
                            </th>
                            <th className="px-4 py-2 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200">
                          {selectedOrder.line_items.map(item => (
                            <tr key={item.id}>
                              <td className="px-4 py-2 text-sm font-medium text-gray-900">
                                {item.title}
                                {item.variant_title && (
                                  <div className="text-xs text-gray-500">{item.variant_title}</div>
                                )}
                              </td>
                              <td className="px-4 py-2 text-sm text-gray-600">{item.sku || 'N/A'}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">{item.quantity}</td>
                              <td className="px-4 py-2 text-sm text-gray-600">${parseFloat(item.price).toFixed(2)}</td>
                            </tr>
                          ))}
                        </tbody>
                      </table>
                    </div>
                  </div>
                )}

                {/* Shipping Address */}
                {selectedOrder.shipping_address && (
                  <div>
                    <h4 className="font-semibold text-gray-900 mb-3">Shipping Address</h4>
                    <div className="text-sm text-gray-700">
                      <div>{selectedOrder.shipping_address.name}</div>
                      <div>{selectedOrder.shipping_address.address1}</div>
                      {selectedOrder.shipping_address.address2 && <div>{selectedOrder.shipping_address.address2}</div>}
                      <div>
                        {selectedOrder.shipping_address.city}, {selectedOrder.shipping_address.province}{' '}
                        {selectedOrder.shipping_address.zip}
                      </div>
                      <div>{selectedOrder.shipping_address.country}</div>
                    </div>
                  </div>
                )}

                <div className="flex space-x-3 pt-4 border-t">
                  <button
                    onClick={() => openInShopify(selectedOrder)}
                    className="flex items-center px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700"
                  >
                    <LinkIcon className="w-4 h-4 mr-2" />
                    Open in Shopify
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ShopifyOrders;
