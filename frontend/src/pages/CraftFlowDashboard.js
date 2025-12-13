import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import {
  ShoppingCartIcon,
  CubeIcon,
  UserGroupIcon,
  CurrencyDollarIcon,
  ChartBarIcon,
  PlusIcon,
  TruckIcon,
  ClockIcon,
} from '@heroicons/react/24/outline';

const CraftFlowDashboard = () => {
  const { token } = useAuth();
  const { addNotification } = useNotifications();
  const navigate = useNavigate();

  const [stats, setStats] = useState(null);
  const [recentOrders, setRecentOrders] = useState([]);
  const [loading, setLoading] = useState(true);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);

      // Fetch dashboard stats
      const [productsRes, ordersRes] = await Promise.all([
        axios.get(`${API_BASE_URL}/api/ecommerce/products/`, {
          headers: { Authorization: `Bearer ${token}` },
        }),
        axios.get(`${API_BASE_URL}/api/ecommerce/orders/`, {
          headers: { Authorization: `Bearer ${token}` },
          params: { page_size: 5 },
        }),
      ]);

      const products = productsRes.data.items || [];
      const orders = ordersRes.data.items || [];

      // Calculate stats
      const totalRevenue = orders.reduce((sum, order) => sum + (order.total || 0), 0);
      const activeProducts = products.filter(p => p.is_active).length;
      const pendingOrders = orders.filter(o => o.status === 'pending' || o.status === 'processing').length;

      setStats({
        totalProducts: products.length,
        activeProducts,
        totalOrders: ordersRes.data.total || orders.length,
        pendingOrders,
        totalRevenue,
        totalCustomers: 0, // TODO: Add customer count
      });

      setRecentOrders(orders);
    } catch (error) {
      console.error('Error loading dashboard:', error);
      addNotification('error', 'Failed to load dashboard data');
    } finally {
      setLoading(false);
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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading dashboard...</p>
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
              CraftFlow Commerce
            </h1>
            <p className="text-gray-600">Manage your online storefront</p>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => navigate('/craftflow/products/create')}
              className="flex items-center px-4 py-2 bg-sage-600 text-white rounded-md hover:bg-sage-700"
            >
              <PlusIcon className="w-4 h-4 mr-2" />
              Add Product
            </button>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          {/* Total Products */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CubeIcon className="h-8 w-8 text-blue-600" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Total Products</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.totalProducts || 0}</p>
                <p className="text-xs text-gray-500 mt-1">{stats?.activeProducts || 0} active</p>
              </div>
            </div>
          </div>

          {/* Total Orders */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <ShoppingCartIcon className="h-8 w-8 text-green-600" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Total Orders</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.totalOrders || 0}</p>
                <p className="text-xs text-gray-500 mt-1">{stats?.pendingOrders || 0} pending</p>
              </div>
            </div>
          </div>

          {/* Total Revenue */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <CurrencyDollarIcon className="h-8 w-8 text-emerald-600" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Total Revenue</p>
                <p className="text-2xl font-bold text-gray-900">${(stats?.totalRevenue || 0).toFixed(2)}</p>
                <p className="text-xs text-gray-500 mt-1">All time</p>
              </div>
            </div>
          </div>

          {/* Customers */}
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <UserGroupIcon className="h-8 w-8 text-purple-600" />
              </div>
              <div className="ml-4 flex-1">
                <p className="text-sm font-medium text-gray-600">Customers</p>
                <p className="text-2xl font-bold text-gray-900">{stats?.totalCustomers || 0}</p>
                <p className="text-xs text-gray-500 mt-1">Registered</p>
              </div>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <button
            onClick={() => navigate('/craftflow/products')}
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <CubeIcon className="h-8 w-8 text-sage-600 mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Manage Products</h3>
            <p className="text-sm text-gray-600">View, edit, and organize your product catalog</p>
          </button>

          <button
            onClick={() => navigate('/craftflow/orders')}
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <TruckIcon className="h-8 w-8 text-sage-600 mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">View Orders</h3>
            <p className="text-sm text-gray-600">Process and fulfill customer orders</p>
          </button>

          <button
            onClick={() => navigate('/craftflow/customers')}
            className="bg-white p-6 rounded-lg shadow hover:shadow-md transition-shadow text-left"
          >
            <UserGroupIcon className="h-8 w-8 text-sage-600 mb-3" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">Customer Management</h3>
            <p className="text-sm text-gray-600">Manage customer accounts and data</p>
          </button>
        </div>

        {/* Recent Orders */}
        <div className="bg-white rounded-lg shadow">
          <div className="px-6 py-4 border-b border-gray-200">
            <div className="flex items-center justify-between">
              <h2 className="text-lg font-semibold text-gray-900">Recent Orders</h2>
              <button
                onClick={() => navigate('/craftflow/orders')}
                className="text-sm text-sage-600 hover:text-sage-700"
              >
                View all →
              </button>
            </div>
          </div>

          <div className="divide-y divide-gray-200">
            {recentOrders.length === 0 ? (
              <div className="px-6 py-8 text-center text-gray-500">
                <ShoppingCartIcon className="h-12 w-12 mx-auto mb-3 text-gray-300" />
                <p>No orders yet</p>
              </div>
            ) : (
              recentOrders.map(order => (
                <div
                  key={order.id}
                  className="px-6 py-4 hover:bg-gray-50 cursor-pointer"
                  onClick={() => navigate(`/craftflow/orders/${order.id}`)}
                >
                  <div className="flex items-center justify-between">
                    <div className="flex-1">
                      <div className="flex items-center">
                        <p className="text-sm font-medium text-gray-900">Order #{order.order_number}</p>
                        <span
                          className={`ml-3 px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(order.status)}`}
                        >
                          {order.status}
                        </span>
                      </div>
                      <p className="text-sm text-gray-500 mt-1">
                        {order.items?.length || 0} items • ${order.total?.toFixed(2)}
                      </p>
                    </div>
                    <div className="flex items-center text-sm text-gray-500">
                      <ClockIcon className="h-4 w-4 mr-1" />
                      {new Date(order.created_at).toLocaleDateString()}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CraftFlowDashboard;
