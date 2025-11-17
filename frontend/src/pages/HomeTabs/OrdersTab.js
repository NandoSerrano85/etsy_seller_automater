import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useApi } from '../../hooks/useApi';

const OrdersTab = ({ isConnected, authUrl, orders, error, onRefresh }) => {
  const [searchParams, setSearchParams] = useSearchParams();
  const activeSubTab = searchParams.get('subtab') || 'all';
  const [expandedOrders, setExpandedOrders] = useState([]);
  const [selectedOrders, setSelectedOrders] = useState([]);
  const [printLoading, setPrintLoading] = useState(false);
  const [printError, setPrintError] = useState(null);
  const [printMsg, setPrintMsg] = useState(null);
  const [packingSlipLoading, setPackingSlipLoading] = useState(false);
  const [csvExporting, setCsvExporting] = useState(false);
  const [showSelectionMode, setShowSelectionMode] = useState(false);
  const [allOrders, setAllOrders] = useState([]);
  const [loadingAllOrders, setLoadingAllOrders] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState('UVDTF 16oz');
  const [orderFilter, setOrderFilter] = useState('active'); // 'active', 'shipped', 'all'
  const [filteredOrders, setFilteredOrders] = useState([]);
  const [loadingOrders, setLoadingOrders] = useState(false);
  const api = useApi();

  // Fetch orders based on filter
  const fetchOrdersByFilter = async filter => {
    setLoadingOrders(true);
    setPrintError(null);
    try {
      let params = {};

      if (filter === 'active') {
        // Active orders: paid, not shipped, not canceled
        params = { was_paid: 'true', was_shipped: 'false', was_canceled: 'false' };
      } else if (filter === 'shipped') {
        // Shipped orders: paid, shipped, not canceled
        params = { was_paid: 'true', was_shipped: 'true', was_canceled: 'false' };
      }
      // 'all' filter: no params, gets all orders

      const queryString = new URLSearchParams(params).toString();
      const url = `/orders${queryString ? `?${queryString}` : ''}`;

      const response = await api.get(url);
      if (response.orders) {
        setFilteredOrders(response.orders);
      } else {
        setPrintError('Failed to load orders');
      }
    } catch (error) {
      setPrintError(error.message || 'Error loading orders');
    } finally {
      setLoadingOrders(false);
    }
  };

  // Handle filter change
  const handleFilterChange = filter => {
    setOrderFilter(filter);
    fetchOrdersByFilter(filter);
  };

  // Load all orders for selection
  const loadAllOrdersForSelection = async () => {
    setLoadingAllOrders(true);
    setPrintError(null);
    try {
      const response = await api.get('/orders/all-orders?limit=100&offset=0');
      if (response.success) {
        setAllOrders(response.orders || []);
        setShowSelectionMode(true);
      } else {
        setPrintError(response.message || 'Failed to load all orders');
      }
    } catch (error) {
      setPrintError(error.message || 'Error loading all orders');
    } finally {
      setLoadingAllOrders(false);
    }
  };

  // Handle order selection
  const handleOrderSelect = orderId => {
    setSelectedOrders(prev => (prev.includes(orderId) ? prev.filter(id => id !== orderId) : [...prev, orderId]));
  };

  // Create print files from selected orders
  const handleCreateFromSelection = async () => {
    if (selectedOrders.length === 0) {
      setPrintError('Please select at least one order');
      return;
    }

    try {
      setPrintLoading(true);
      setPrintError(null);
      setPrintMsg(null);

      console.log('🔵 Sending request:', {
        template_name: selectedTemplate,
        order_ids: selectedOrders,
        order_ids_type: typeof selectedOrders,
        order_ids_is_array: Array.isArray(selectedOrders),
        order_ids_length: selectedOrders.length,
      });
      console.log(JSON.stringify({ template_name: selectedTemplate, order_ids: selectedOrders }));
      const response = await api.post('/orders/print-files-from-selection', {
        template_name: selectedTemplate,
        order_ids: selectedOrders,
      });

      console.log('🟢 Received response:', response);
      if (response.success) {
        setPrintMsg(
          `Created ${response.sheets_created} gang sheets from ${response.orders_processed} orders. Files uploaded to NAS.`
        );
        setSelectedOrders([]);
        setShowSelectionMode(false);
      } else {
        setPrintError(response.message || 'Failed to create print files');
      }
    } catch (error) {
      setPrintError(error.message || 'Error creating print files from selection');
    } finally {
      setPrintLoading(false);
    }
  };

  // Export CSV of selected orders
  const handleExportCSV = async () => {
    if (selectedOrders.length === 0) {
      setPrintError('Please select at least one order');
      return;
    }

    setCsvExporting(true);
    setPrintError(null);
    try {
      // Get selected orders from the allOrders array
      const selectedOrdersData = allOrders.filter(order => selectedOrders.includes(order.order_id));

      // Aggregate design quantities
      const designQuantities = {};

      selectedOrdersData.forEach(order => {
        if (order && order.items) {
          order.items.forEach(item => {
            // Extract design name from item title (e.g., "UV 840 | UVDTF Cup wrap" -> "UV 840")
            const itemTitle = item.title || '';
            const match = itemTitle.match(/^(UV\s*\d+)/i);

            if (match) {
              const designName = match[1].trim();
              const quantity = item.quantity || 1;

              if (designQuantities[designName]) {
                designQuantities[designName] += quantity;
              } else {
                designQuantities[designName] = quantity;
              }
            }
          });
        }
      });

      // Create CSV content
      const csvRows = [];
      csvRows.push(['Product title', 'Type', 'Total'].join(','));

      Object.entries(designQuantities).forEach(([designName, total]) => {
        csvRows.push([`"${designName}"`, `"${selectedTemplate}"`, total].join(','));
      });

      const csvContent = csvRows.join('\n');

      // Download CSV
      const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `etsy-print-order-${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      window.URL.revokeObjectURL(url);

      setPrintMsg('CSV exported successfully');
    } catch (error) {
      console.error('Error exporting CSV:', error);
      setPrintError(error.message || 'Failed to export CSV');
    } finally {
      setCsvExporting(false);
    }
  };

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
        // setSelectedOrders([]);
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

  // Add packing slip generation function
  const handleGeneratePackingSlips = async () => {
    console.log('🔵 Packing slip button clicked!', { ordersLength: orders.length });

    if (orders.length === 0) {
      setPrintError('No orders available to generate packing slips');
      return;
    }

    try {
      setPackingSlipLoading(true);
      setPrintError(null);
      setPrintMsg(null);

      console.log('Fetching packing slips from:', `${api.baseUrl}/api/packing-slip/bulk/etsy-orders`);

      // Fetch the PDF from the API using authenticated fetchFile
      const response = await api.fetchFile('/api/packing-slip/bulk/etsy-orders', {
        method: 'GET',
      });

      console.log('Response status:', response.status);
      console.log('Response content-type:', response.headers.get('content-type'));

      // Get the PDF blob
      const blob = await response.blob();
      console.log('Blob size:', blob.size, 'Blob type:', blob.type);

      // Verify we got a PDF
      if (blob.type !== 'application/pdf' && blob.type !== '') {
        // If we got HTML, read it to see the error
        const text = await blob.text();
        console.error('Received non-PDF response:', text.substring(0, 500));
        throw new Error(`Expected PDF but got ${blob.type}. Check console for details.`);
      }

      if (blob.size === 0) {
        throw new Error('Received empty PDF file');
      }

      // Open PDF in new tab for viewing/printing
      const url = window.URL.createObjectURL(blob);
      window.open(url, '_blank');

      setPrintMsg(`Successfully generated packing slips for ${orders.length} orders`);
    } catch (error) {
      setPrintError(error.message || 'Error generating packing slips');
      console.error('Packing slip error:', error);
    } finally {
      setPackingSlipLoading(false);
    }
  };

  // Add print tab content
  const renderPrintTab = () => {
    return (
      <div className="space-y-6">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex justify-between items-center mb-6">
            <h3 className="text-lg font-semibold">
              {showSelectionMode ? 'Select Orders for Print' : 'Selected Orders for Print'}
            </h3>
            <div className="flex gap-3">
              {showSelectionMode && (
                <>
                  <select
                    value={selectedTemplate}
                    onChange={e => setSelectedTemplate(e.target.value)}
                    className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-lavender-500"
                  >
                    <option value="UVDTF 16oz">UVDTF 16oz</option>
                    <option value="UVDTF 12oz">UVDTF 12oz</option>
                    <option value="UVDTF Misc">UVDTF Misc</option>
                  </select>
                  <button
                    onClick={handleCreateFromSelection}
                    disabled={selectedOrders.length === 0 || printLoading}
                    className={`
                      px-4 py-2 rounded-lg font-medium flex items-center space-x-2
                      ${
                        selectedOrders.length === 0 || printLoading
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
                        <span>Create Print Files ({selectedOrders.length})</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleExportCSV}
                    disabled={selectedOrders.length === 0 || csvExporting}
                    className={`
                      px-4 py-2 rounded-lg font-medium flex items-center space-x-2
                      ${
                        selectedOrders.length === 0 || csvExporting
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-500 text-white hover:bg-blue-600'
                      }
                    `}
                  >
                    {csvExporting ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <span>📥</span>
                        <span>Export CSV ({selectedOrders.length})</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={() => {
                      setShowSelectionMode(false);
                      setSelectedOrders([]);
                      setAllOrders([]);
                    }}
                    className="px-4 py-2 rounded-lg font-medium bg-gray-200 text-gray-700 hover:bg-gray-300"
                  >
                    Cancel
                  </button>
                </>
              )}
              {!showSelectionMode && (
                <>
                  <button
                    onClick={loadAllOrdersForSelection}
                    disabled={loadingAllOrders}
                    className={`
                      px-4 py-2 rounded-lg font-medium flex items-center space-x-2
                      ${
                        loadingAllOrders
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-green-500 text-white hover:bg-green-600'
                      }
                    `}
                  >
                    {loadingAllOrders ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <span>📋</span>
                        <span>Select Orders</span>
                      </>
                    )}
                  </button>
                  <button
                    onClick={handleGeneratePackingSlips}
                    disabled={orders.length === 0 || packingSlipLoading}
                    className={`
                      px-4 py-2 rounded-lg font-medium flex items-center space-x-2
                      ${
                        orders.length === 0 || packingSlipLoading
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : 'bg-blue-500 text-white hover:bg-blue-600'
                      }
                    `}
                  >
                    {packingSlipLoading ? (
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                    ) : (
                      <>
                        <span>📄</span>
                        <span>Packing Slips ({orders.length})</span>
                      </>
                    )}
                  </button>
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
                </>
              )}
            </div>
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
                  {showSelectionMode && <th className="px-4 py-2 text-left">Select</th>}
                  <th className="px-4 py-2 text-left">Order ID</th>
                  <th className="px-4 py-2 text-left">Customer</th>
                  <th className="px-4 py-2 text-left">Items</th>
                  {showSelectionMode && <th className="px-4 py-2 text-left">Order Date</th>}
                </tr>
              </thead>
              <tbody>
                {(showSelectionMode ? allOrders : orders).map(order => (
                  <tr key={order.order_id} className="border-b border-gray-100 hover:bg-gray-50">
                    {showSelectionMode && (
                      <td className="px-4 py-2">
                        <input
                          type="checkbox"
                          checked={selectedOrders.includes(order.order_id)}
                          onChange={() => handleOrderSelect(order.order_id)}
                          className="rounded border-gray-300 text-lavender-600 focus:ring-lavender-500"
                        />
                      </td>
                    )}
                    <td className="px-4 py-2">{order.order_id}</td>
                    <td className="px-4 py-2">{order.customer_name || 'N/A'}</td>
                    <td className="px-4 py-2">
                      {order.items?.reduce((total, item) => total + (item.quantity || 0), 0) || 0}
                    </td>
                    {showSelectionMode && (
                      <td className="px-4 py-2">{new Date(order.order_date * 1000).toLocaleDateString()}</td>
                    )}
                  </tr>
                ))}
              </tbody>
            </table>
            {showSelectionMode && allOrders.length === 0 && (
              <div className="text-center py-8 text-gray-500">No orders available</div>
            )}
            {!showSelectionMode && orders.length === 0 && (
              <div className="text-center py-8 text-gray-500">No orders selected for print</div>
            )}
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
            <h3 className="text-2xl font-bold text-gray-900">
              {(filteredOrders.length > 0 ? filteredOrders : orders || []).length}
            </h3>
            <p className="text-gray-600">
              {orderFilter === 'active' && 'Active Orders'}
              {orderFilter === 'shipped' && 'Shipped Orders'}
              {orderFilter === 'all' && 'All Orders'}
            </p>
          </div>
          <div className="text-center">
            <h3 className="text-2xl font-bold text-gray-900">
              {(filteredOrders.length > 0 ? filteredOrders : orders || []).reduce(
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
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-bold text-gray-900">Orders</h2>
          <div className="flex gap-2">
            <button
              onClick={() => handleFilterChange('active')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                orderFilter === 'active' ? 'bg-lavender-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Active Orders
            </button>
            <button
              onClick={() => handleFilterChange('shipped')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                orderFilter === 'shipped' ? 'bg-lavender-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              Shipped Orders
            </button>
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-4 py-2 rounded-lg font-medium transition-colors ${
                orderFilter === 'all' ? 'bg-lavender-500 text-white' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              All Orders
            </button>
          </div>
        </div>

        {loadingOrders && (
          <div className="flex items-center justify-center p-8">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-lavender-500"></div>
            <span className="ml-2 text-gray-600">Loading orders...</span>
          </div>
        )}

        {!loadingOrders && (
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
                {(filteredOrders.length > 0 ? filteredOrders : orders || []).map(order => (
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
            {(filteredOrders.length > 0 ? filteredOrders : orders || []).length === 0 && (
              <div className="text-center py-8 text-gray-500">
                {orderFilter === 'active' && 'No active orders found'}
                {orderFilter === 'shipped' && 'No shipped orders found'}
                {orderFilter === 'all' && 'No orders found'}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default OrdersTab;
