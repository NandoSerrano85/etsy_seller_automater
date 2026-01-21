import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { useNotifications } from '../components/NotificationSystem';
import axios from 'axios';
import {
  ArrowLeftIcon,
  ShoppingCartIcon,
  UserIcon,
  TruckIcon,
  CreditCardIcon,
  ClockIcon,
  CheckCircleIcon,
  XCircleIcon,
  DocumentArrowDownIcon,
  PrinterIcon,
  MapPinIcon,
  EnvelopeIcon,
  PhoneIcon,
  TagIcon,
  CubeIcon,
  ScaleIcon,
} from '@heroicons/react/24/outline';

const CraftFlowOrderDetails = () => {
  const { id } = useParams();
  const navigate = useNavigate();
  const { userToken: token } = useAuth();
  const { addNotification } = useNotifications();

  const [order, setOrder] = useState(null);
  const [loading, setLoading] = useState(true);
  const [shippingRates, setShippingRates] = useState([]);
  const [loadingRates, setLoadingRates] = useState(false);
  const [selectedRate, setSelectedRate] = useState(null);
  const [creatingLabel, setCreatingLabel] = useState(false);
  const [showRatesModal, setShowRatesModal] = useState(false);

  // Package dimensions state
  const [packageDimensions, setPackageDimensions] = useState({
    length: '10',
    width: '8',
    height: '4',
    weight: '1',
  });
  const [showDimensionsStep, setShowDimensionsStep] = useState(true);

  const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';

  useEffect(() => {
    loadOrder();
  }, [id]);

  const loadOrder = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/orders/${id}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setOrder(response.data);
    } catch (error) {
      console.error('Error loading order:', error);
      addNotification('error', 'Failed to load order details');
    } finally {
      setLoading(false);
    }
  };

  const openShippingModal = () => {
    setShowRatesModal(true);
    setShowDimensionsStep(true);
    setShippingRates([]);
    setSelectedRate(null);
  };

  const loadShippingRates = async () => {
    try {
      setLoadingRates(true);
      const params = new URLSearchParams({
        length: packageDimensions.length,
        width: packageDimensions.width,
        height: packageDimensions.height,
        weight: packageDimensions.weight,
      });

      const response = await axios.get(`${API_BASE_URL}/api/ecommerce/admin/orders/${id}/shipping-rates?${params}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      setShippingRates(response.data);
      setShowDimensionsStep(false);
    } catch (error) {
      console.error('Error loading shipping rates:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to load shipping rates');
    } finally {
      setLoadingRates(false);
    }
  };

  const createLabel = async () => {
    if (!selectedRate) {
      addNotification('error', 'Please select a shipping rate');
      return;
    }

    try {
      setCreatingLabel(true);
      const response = await axios.post(
        `${API_BASE_URL}/api/ecommerce/admin/orders/${id}/create-label`,
        {
          rate_id: selectedRate.rate_id,
          label_file_type: 'PDF',
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      addNotification('success', `Label created! Tracking: ${response.data.tracking_number}`);

      // Open label URL in new tab if available
      if (response.data.label_url) {
        window.open(response.data.label_url, '_blank');
      }

      // Reload order to show updated tracking info
      setShowRatesModal(false);
      loadOrder();
    } catch (error) {
      console.error('Error creating label:', error);
      addNotification('error', error.response?.data?.detail || 'Failed to create shipping label');
    } finally {
      setCreatingLabel(false);
    }
  };

  const handleUpdateStatus = async newStatus => {
    try {
      await axios.put(
        `${API_BASE_URL}/api/ecommerce/admin/orders/${id}`,
        { status: newStatus },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      addNotification('success', `Order status updated to ${newStatus}`);
      loadOrder();
    } catch (error) {
      console.error('Error updating order status:', error);
      addNotification('error', 'Failed to update order status');
    }
  };

  const handleDimensionChange = (field, value) => {
    setPackageDimensions(prev => ({
      ...prev,
      [field]: value,
    }));
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

  const getPaymentStatusColor = status => {
    const colors = {
      paid: 'bg-green-100 text-green-800',
      pending: 'bg-yellow-100 text-yellow-800',
      failed: 'bg-red-100 text-red-800',
      refunded: 'bg-gray-100 text-gray-800',
    };
    return colors[status] || 'bg-gray-100 text-gray-800';
  };

  const getStatusIcon = status => {
    switch (status) {
      case 'pending':
        return <ClockIcon className="w-5 h-5" />;
      case 'processing':
        return <ClockIcon className="w-5 h-5" />;
      case 'shipped':
        return <TruckIcon className="w-5 h-5" />;
      case 'delivered':
        return <CheckCircleIcon className="w-5 h-5" />;
      case 'cancelled':
        return <XCircleIcon className="w-5 h-5" />;
      default:
        return <ClockIcon className="w-5 h-5" />;
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-sage-600 mx-auto mb-4"></div>
          <p className="text-sage-600">Loading order details...</p>
        </div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <ShoppingCartIcon className="h-12 w-12 mx-auto text-gray-300 mb-3" />
          <p className="text-gray-500">Order not found</p>
          <button
            onClick={() => navigate('/craftflow/orders')}
            className="mt-4 text-sage-600 hover:text-sage-800 font-medium"
          >
            ← Back to Orders
          </button>
        </div>
      </div>
    );
  }

  const shippingAddress = order.shipping_address || {};

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto py-6 px-6">
        {/* Header */}
        <div className="mb-6">
          <button
            onClick={() => navigate('/craftflow/orders')}
            className="flex items-center text-sage-600 hover:text-sage-800 mb-4"
          >
            <ArrowLeftIcon className="w-5 h-5 mr-2" />
            Back to Orders
          </button>

          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-gray-900 flex items-center">
                <ShoppingCartIcon className="w-8 h-8 mr-3 text-sage-600" />
                Order #{order.order_number}
              </h1>
              <p className="text-gray-600">
                Placed on {new Date(order.created_at).toLocaleDateString()} at{' '}
                {new Date(order.created_at).toLocaleTimeString()}
              </p>
            </div>

            <div className="flex items-center gap-3">
              {/* Status Badge */}
              <span
                className={`inline-flex items-center gap-1 px-3 py-1 text-sm font-semibold rounded-full ${getStatusColor(order.status)}`}
              >
                {getStatusIcon(order.status)}
                {order.status}
              </span>

              {/* Payment Status */}
              <span
                className={`inline-flex items-center gap-1 px-3 py-1 text-sm font-semibold rounded-full ${getPaymentStatusColor(order.payment_status)}`}
              >
                <CreditCardIcon className="w-4 h-4" />
                {order.payment_status}
              </span>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Main Content - Left 2 Columns */}
          <div className="lg:col-span-2 space-y-6">
            {/* Order Items */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <TagIcon className="w-5 h-5 mr-2 text-sage-600" />
                Order Items ({order.items?.length || 0})
              </h2>

              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                      <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">SKU</th>
                      <th className="px-4 py-3 text-center text-xs font-medium text-gray-500 uppercase">Qty</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Price</th>
                      <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total</th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {order.items?.map((item, index) => (
                      <tr key={item.id || index}>
                        <td className="px-4 py-4">
                          <div className="text-sm font-medium text-gray-900">{item.product_name}</div>
                          {item.variant_name && <div className="text-sm text-gray-500">{item.variant_name}</div>}
                        </td>
                        <td className="px-4 py-4 text-sm text-gray-500">{item.sku || '-'}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 text-center">{item.quantity}</td>
                        <td className="px-4 py-4 text-sm text-gray-900 text-right">${item.price?.toFixed(2)}</td>
                        <td className="px-4 py-4 text-sm font-medium text-gray-900 text-right">
                          ${item.total?.toFixed(2)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* Order Totals */}
              <div className="mt-4 border-t pt-4">
                <div className="flex justify-end">
                  <div className="w-64 space-y-2">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Subtotal:</span>
                      <span className="text-gray-900">${order.subtotal?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Shipping:</span>
                      <span className="text-gray-900">${order.shipping?.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Tax:</span>
                      <span className="text-gray-900">${order.tax?.toFixed(2)}</span>
                    </div>
                    {order.discount > 0 && (
                      <div className="flex justify-between text-sm">
                        <span className="text-gray-600">Discount:</span>
                        <span className="text-green-600">-${order.discount?.toFixed(2)}</span>
                      </div>
                    )}
                    <div className="flex justify-between text-lg font-bold border-t pt-2">
                      <span>Total:</span>
                      <span>${order.total?.toFixed(2)}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Shipping Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold text-gray-900 flex items-center">
                  <TruckIcon className="w-5 h-5 mr-2 text-sage-600" />
                  Shipping Information
                </h2>

                {!order.tracking_number && order.payment_status === 'paid' && (
                  <button
                    onClick={openShippingModal}
                    className="flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700"
                  >
                    <PrinterIcon className="w-5 h-5" />
                    Create Shipping Label
                  </button>
                )}
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Shipping Address */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                    <MapPinIcon className="w-4 h-4 mr-1" />
                    Shipping Address
                  </h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    <p className="font-medium">
                      {shippingAddress.first_name} {shippingAddress.last_name}
                    </p>
                    <p className="text-gray-600">{shippingAddress.address1}</p>
                    {shippingAddress.address2 && <p className="text-gray-600">{shippingAddress.address2}</p>}
                    <p className="text-gray-600">
                      {shippingAddress.city}, {shippingAddress.state} {shippingAddress.zip_code}
                    </p>
                    <p className="text-gray-600">{shippingAddress.country || 'United States'}</p>
                    {shippingAddress.phone && (
                      <p className="text-gray-600 mt-2 flex items-center">
                        <PhoneIcon className="w-4 h-4 mr-1" />
                        {shippingAddress.phone}
                      </p>
                    )}
                  </div>
                </div>

                {/* Tracking Info */}
                <div>
                  <h3 className="text-sm font-medium text-gray-700 mb-2">Tracking Information</h3>
                  <div className="bg-gray-50 rounded-lg p-4">
                    {order.tracking_number ? (
                      <>
                        <p className="font-medium text-green-700 flex items-center">
                          <CheckCircleIcon className="w-5 h-5 mr-2" />
                          Label Created
                        </p>
                        <p className="text-gray-600 mt-2">
                          <span className="font-medium">Tracking #:</span> {order.tracking_number}
                        </p>
                        {order.tracking_url && (
                          <a
                            href={order.tracking_url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sage-600 hover:text-sage-800 text-sm mt-2 inline-block"
                          >
                            Track Package →
                          </a>
                        )}
                      </>
                    ) : (
                      <p className="text-gray-500 flex items-center">
                        <ClockIcon className="w-5 h-5 mr-2" />
                        No tracking information yet
                      </p>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Sidebar - Right Column */}
          <div className="space-y-6">
            {/* Customer Information */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4 flex items-center">
                <UserIcon className="w-5 h-5 mr-2 text-sage-600" />
                Customer
              </h2>

              <div className="space-y-3">
                <div>
                  <p className="font-medium text-gray-900">{order.customer_name || 'Guest Customer'}</p>
                  {order.customer_email && (
                    <p className="text-gray-600 flex items-center mt-1">
                      <EnvelopeIcon className="w-4 h-4 mr-1" />
                      {order.customer_email}
                    </p>
                  )}
                </div>

                {order.customer_id && <p className="text-xs text-gray-500">Customer ID: {order.customer_id}</p>}
              </div>
            </div>

            {/* Order Actions */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Actions</h2>

              <div className="space-y-3">
                {/* Update Status */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Update Status</label>
                  <select
                    value={order.status}
                    onChange={e => handleUpdateStatus(e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-sage-500 focus:border-sage-500"
                  >
                    <option value="pending">Pending</option>
                    <option value="processing">Processing</option>
                    <option value="shipped">Shipped</option>
                    <option value="delivered">Delivered</option>
                    <option value="cancelled">Cancelled</option>
                  </select>
                </div>

                {/* Quick Actions */}
                {order.tracking_number && (
                  <button
                    onClick={() => window.open(order.tracking_url, '_blank')}
                    className="w-full flex items-center justify-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    <TruckIcon className="w-5 h-5" />
                    Track Package
                  </button>
                )}
              </div>
            </div>

            {/* Order Timeline */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-bold text-gray-900 mb-4">Timeline</h2>

              <div className="space-y-4">
                <div className="flex items-start">
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                    <CheckCircleIcon className="w-5 h-5 text-green-600" />
                  </div>
                  <div className="ml-3">
                    <p className="text-sm font-medium text-gray-900">Order Placed</p>
                    <p className="text-xs text-gray-500">{new Date(order.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {order.payment_status === 'paid' && (
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <CreditCardIcon className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Payment Received</p>
                      <p className="text-xs text-gray-500">via {order.payment_method || 'Stripe'}</p>
                    </div>
                  </div>
                )}

                {order.tracking_number && (
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-purple-100 flex items-center justify-center">
                      <TruckIcon className="w-5 h-5 text-purple-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Shipped</p>
                      <p className="text-xs text-gray-500">Tracking: {order.tracking_number}</p>
                    </div>
                  </div>
                )}

                {order.status === 'delivered' && (
                  <div className="flex items-start">
                    <div className="flex-shrink-0 w-8 h-8 rounded-full bg-green-100 flex items-center justify-center">
                      <CheckCircleIcon className="w-5 h-5 text-green-600" />
                    </div>
                    <div className="ml-3">
                      <p className="text-sm font-medium text-gray-900">Delivered</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Shipping Label Modal */}
      {showRatesModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full mx-4 max-h-[90vh] overflow-hidden">
            {/* Modal Header */}
            <div className="p-6 border-b">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-gray-900">
                  {showDimensionsStep ? 'Package Details' : 'Select Shipping Rate'}
                </h3>
                <button onClick={() => setShowRatesModal(false)} className="text-gray-400 hover:text-gray-600">
                  <XCircleIcon className="w-6 h-6" />
                </button>
              </div>
              {/* Step Indicator */}
              <div className="flex items-center mt-4">
                <div className={`flex items-center ${showDimensionsStep ? 'text-sage-600' : 'text-gray-400'}`}>
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      showDimensionsStep ? 'bg-sage-600 text-white' : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    1
                  </div>
                  <span className="ml-2 text-sm font-medium">Package Info</span>
                </div>
                <div className="flex-1 h-0.5 bg-gray-200 mx-4"></div>
                <div className={`flex items-center ${!showDimensionsStep ? 'text-sage-600' : 'text-gray-400'}`}>
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      !showDimensionsStep ? 'bg-sage-600 text-white' : 'bg-gray-200 text-gray-600'
                    }`}
                  >
                    2
                  </div>
                  <span className="ml-2 text-sm font-medium">Select Rate</span>
                </div>
              </div>
            </div>

            {/* Modal Content */}
            <div className="p-6 overflow-y-auto max-h-[60vh]">
              {showDimensionsStep ? (
                /* Step 1: Package Dimensions */
                <div className="space-y-6">
                  <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <p className="text-sm text-blue-800">
                      <strong>Tip:</strong> Enter accurate package dimensions and weight to get the most accurate
                      shipping rates.
                    </p>
                  </div>

                  {/* Dimensions */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                      <CubeIcon className="w-5 h-5 mr-2 text-gray-500" />
                      Package Dimensions (inches)
                    </h4>
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Length</label>
                        <input
                          type="number"
                          min="0.1"
                          max="100"
                          step="0.1"
                          value={packageDimensions.length}
                          onChange={e => handleDimensionChange('length', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-sage-500 focus:border-sage-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Width</label>
                        <input
                          type="number"
                          min="0.1"
                          max="100"
                          step="0.1"
                          value={packageDimensions.width}
                          onChange={e => handleDimensionChange('width', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-sage-500 focus:border-sage-500"
                        />
                      </div>
                      <div>
                        <label className="block text-xs text-gray-500 mb-1">Height</label>
                        <input
                          type="number"
                          min="0.1"
                          max="100"
                          step="0.1"
                          value={packageDimensions.height}
                          onChange={e => handleDimensionChange('height', e.target.value)}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-sage-500 focus:border-sage-500"
                        />
                      </div>
                    </div>
                  </div>

                  {/* Weight */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3 flex items-center">
                      <ScaleIcon className="w-5 h-5 mr-2 text-gray-500" />
                      Package Weight
                    </h4>
                    <div className="flex items-center gap-3">
                      <input
                        type="number"
                        min="0.1"
                        max="150"
                        step="0.1"
                        value={packageDimensions.weight}
                        onChange={e => handleDimensionChange('weight', e.target.value)}
                        className="w-32 px-3 py-2 border border-gray-300 rounded-lg focus:ring-sage-500 focus:border-sage-500"
                      />
                      <span className="text-gray-600">lbs</span>
                    </div>
                  </div>

                  {/* Quick Presets */}
                  <div>
                    <h4 className="text-sm font-medium text-gray-700 mb-3">Quick Presets</h4>
                    <div className="flex flex-wrap gap-2">
                      <button
                        onClick={() => setPackageDimensions({ length: '6', width: '4', height: '2', weight: '0.5' })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        Small (6×4×2)
                      </button>
                      <button
                        onClick={() => setPackageDimensions({ length: '10', width: '8', height: '4', weight: '1' })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        Medium (10×8×4)
                      </button>
                      <button
                        onClick={() => setPackageDimensions({ length: '14', width: '12', height: '6', weight: '2' })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        Large (14×12×6)
                      </button>
                      <button
                        onClick={() => setPackageDimensions({ length: '18', width: '14', height: '8', weight: '5' })}
                        className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50"
                      >
                        X-Large (18×14×8)
                      </button>
                    </div>
                  </div>
                </div>
              ) : (
                /* Step 2: Shipping Rates */
                <div>
                  {/* Package Summary */}
                  <div className="bg-gray-50 rounded-lg p-3 mb-4">
                    <p className="text-sm text-gray-600">
                      <span className="font-medium">Package:</span> {packageDimensions.length}" ×{' '}
                      {packageDimensions.width}" × {packageDimensions.height}" • {packageDimensions.weight} lbs
                      <button
                        onClick={() => setShowDimensionsStep(true)}
                        className="ml-2 text-sage-600 hover:text-sage-800 text-xs"
                      >
                        Edit
                      </button>
                    </p>
                  </div>

                  {shippingRates.length === 0 ? (
                    <p className="text-gray-500 text-center py-8">No shipping rates available</p>
                  ) : (
                    <div className="space-y-3">
                      {shippingRates.map((rate, index) => (
                        <div
                          key={rate.rate_id || index}
                          onClick={() => setSelectedRate(rate)}
                          className={`border rounded-lg p-4 cursor-pointer transition-all ${
                            selectedRate?.rate_id === rate.rate_id
                              ? 'border-sage-600 bg-sage-50 shadow-md'
                              : 'border-gray-200 hover:border-sage-300 hover:bg-gray-50'
                          }`}
                        >
                          <div className="flex items-center justify-between">
                            <div>
                              <p className="font-medium text-gray-900">
                                {rate.carrier} - {rate.service}
                              </p>
                              <p className="text-sm text-gray-600">{rate.duration_terms}</p>
                              {rate.estimated_days && (
                                <p className="text-xs text-gray-500">
                                  Est. {rate.estimated_days} business day{rate.estimated_days !== 1 ? 's' : ''}
                                </p>
                              )}
                              {rate.is_fallback && (
                                <span className="inline-block mt-1 text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                                  Estimated Rate
                                </span>
                              )}
                            </div>
                            <div className="text-right">
                              <p className="text-xl font-bold text-gray-900">${rate.amount?.toFixed(2)}</p>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="p-6 border-t bg-gray-50">
              <div className="flex items-center justify-between">
                <div>
                  {!showDimensionsStep && selectedRate && (
                    <p className="text-sm text-gray-600">
                      Selected: {selectedRate.carrier} - {selectedRate.service} ($
                      {selectedRate.amount?.toFixed(2)})
                    </p>
                  )}
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={() => setShowRatesModal(false)}
                    className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
                  >
                    Cancel
                  </button>

                  {showDimensionsStep ? (
                    <button
                      onClick={loadShippingRates}
                      disabled={loadingRates}
                      className="flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50"
                    >
                      {loadingRates ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Loading Rates...
                        </>
                      ) : (
                        <>Get Shipping Rates</>
                      )}
                    </button>
                  ) : (
                    <button
                      onClick={createLabel}
                      disabled={!selectedRate || creatingLabel || selectedRate?.is_fallback}
                      className="flex items-center gap-2 px-4 py-2 bg-sage-600 text-white rounded-lg hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {creatingLabel ? (
                        <>
                          <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                          Creating Label...
                        </>
                      ) : (
                        <>
                          <DocumentArrowDownIcon className="w-5 h-5" />
                          Purchase Label
                        </>
                      )}
                    </button>
                  )}
                </div>
              </div>
              {!showDimensionsStep && selectedRate?.is_fallback && (
                <p className="text-xs text-yellow-700 mt-2">
                  Cannot create labels with estimated rates. Please configure your Shippo API key for real rates.
                </p>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CraftFlowOrderDetails;
