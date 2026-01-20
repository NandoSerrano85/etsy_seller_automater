import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import {
  ShoppingCartIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  TruckIcon,
} from '@heroicons/react/24/outline';

const CraftFlowOrders = () => {
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [orders, setOrders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadOrders();
  }, []);

  const loadOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/orders/`, {
        headers: { Authorization: `Bearer ${token}` },
        params: { page_size: 100 },
      });

      setOrders(response.data.items || []);
    } catch (error) {
      console.error('Error loading orders:', error);
      addNotification('error', 'Failed to load orders');
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateStatus = async (orderId, newStatus) => {
    try {
      await axios.put(
        `${API_BASE_URL}/api/ecommerce/admin/orders/${orderId}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      addNotification('success', `Order status updated to ${newStatus}`);
      loadOrders();
    } catch (error) {
      console.error('Error updating order status:', error);
      addNotification('error', 'Failed to update order status');
    }
  };

  const getStatusColor = status => {
    const colors = {
      pending: 'bg-yellow-100 text-yellow-800',
      processing: 'bg-blue-100 text-blue-800',
      shipped: 'bg-purple-100 text-purple-800',
      delivered: 'bg-green-100 text-green-800',
      cancelled: 'bg-red-100 text-red-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-4 h-4" />;
      case 'processing':
        return <ClockIcon className="w-4 h-4" />;
      case 'shipped':
        return <TruckIcon className="w-4 h-4" />;
      case 'delivered':
        return <CheckCircleIcon className="w-4 h-4" />;
      case 'cancelled':
        return <XCircleIcon className="w-4 h-4" />;
      default:
        return <ClockIcon className="w-4 h-4" />;
    }
  };

  // Filter orders
  const filteredOrders = orders.filter(order => {
    const matchesSearch =
      order.order_number?.toString().includes(searchTerm) ||
      order.customer_email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      order.customer_name?.toLowerCase().includes(searchTerm.toLowerCase());

    const matchesStatus = statusFilter === 'all' || order.status === statusFilter;

    return matchesSearch && matchesStatus;
  });

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
            <h1 className="text-2xl font-bold text-gray-900 flex items-center">
              <ShoppingCartIcon className="w-8 h-8 mr-3 text-sage-600" />
              Orders
            </h1>
            <p className="text-gray-600">{filteredOrders.length} orders</p>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-lg shadow mb-6 p-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Search */}
            <div className="relative">
              <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search orders..."
                value={searchTerm}
                onChange={e => setSearchTerm(e.target.value)}
                className="pl-10 pr-4 py-2 w-full border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
              />
            </div>

            {/* Status Filter */}
            <select
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-md focus:ring-sage-500 focus:border-sage-500"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="processing">Processing</option>
              <option value="shipped">Shipped</option>
              <option value="delivered">Delivered</option>
              <option value="cancelled">Cancelled</option>
            </select>
          </div>
        </div>

        {/* Orders Table */}
        <div className="bg-white rounded-lg shadow overflow-y-auto">
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
                  Items
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Total
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Status
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {filteredOrders.length === 0 ? (
                <tr>
                  <td colSpan="7" className="px-6 py-12 text-center">
                    <ShoppingCartIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
                    <p className="text-gray-500">No orders found</p>
                  </td>
                </tr>
              ) : (
                filteredOrders.map(order => (
                  <tr key={order.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">#{order.order_number}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{order.customer_name || 'Guest'}</div>
                      <div className="text-sm text-gray-500">{order.customer_email}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {order.items?.length || 0} items
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm font-medium text-gray-900">${order.total?.toFixed(2) || '0.00'}</div>
                      {order.payment_status && (
                        <div className="text-xs text-gray-500">Payment: {order.payment_status}</div>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <select
                        value={order.status}
                        onChange={e => handleUpdateStatus(order.id, e.target.value)}
                        className={`px-2 py-1 text-xs font-semibold rounded-full border-0 focus:ring-2 focus:ring-sage-500 ${getStatusColor(
                          order.status
                        )}`}
                      >
                        <option value="pending">Pending</option>
                        <option value="processing">Processing</option>
                        <option value="shipped">Shipped</option>
                        <option value="delivered">Delivered</option>
                        <option value="cancelled">Cancelled</option>
                      </select>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(order.created_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <button
                        onClick={() => navigate(`/craftflow/orders/${order.id}`)}
                        className="text-sage-600 hover:text-sage-900"
                        title="View order details"
                      >
                        <EyeIcon className="h-5 w-5" />
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>

        {/* Order Stats */}
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-yellow-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">Pending</p>
                <p className="text-xl font-bold text-gray-900">{orders.filter(o => o.status === 'pending').length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <ClockIcon className="h-8 w-8 text-blue-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">Processing</p>
                <p className="text-xl font-bold text-gray-900">
                  {orders.filter(o => o.status === 'processing').length}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <TruckIcon className="h-8 w-8 text-purple-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">Shipped</p>
                <p className="text-xl font-bold text-gray-900">{orders.filter(o => o.status === 'shipped').length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-4">
            <div className="flex items-center">
              <CheckCircleIcon className="h-8 w-8 text-green-600" />
              <div className="ml-3">
                <p className="text-sm text-gray-600">Delivered</p>
                <p className="text-xl font-bold text-gray-900">{orders.filter(o => o.status === 'delivered').length}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CraftFlowOrders;
