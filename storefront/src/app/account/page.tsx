"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { ordersApi } from "@/lib/api";
import { useStore } from "@/store/useStore";
import { Order } from "@/types";
import { formatPrice, formatDate } from "@/lib/utils";
import {
  Package,
  ShoppingBag,
  Clock,
  CheckCircle,
  ArrowRight,
} from "lucide-react";

export default function AccountPage() {
  const { customer } = useStore();
  const [recentOrders, setRecentOrders] = useState<Order[]>([]);
  const [stats, setStats] = useState({
    totalOrders: 0,
    pendingOrders: 0,
    completedOrders: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchAccountData();
  }, []);

  const fetchAccountData = async () => {
    setIsLoading(true);
    try {
      const response = await ordersApi.getAll({ page_size: 5 });
      const orders = response.items || [];
      setRecentOrders(orders);

      // Calculate stats
      const totalOrders = response.total || orders.length;
      // const pendingOrders = orders.filter(
      //   (order) => order.status === "pending" || order.status === "processing",
      // ).length;
      const pendingOrders = orders.filter(
        (order) => order.status === "processing",
      ).length;
      const completedOrders = orders.filter(
        (order) => order.status === "delivered",
      ).length;

      setStats({ totalOrders, pendingOrders, completedOrders });
    } catch (error) {
      console.error("Failed to fetch account data:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "delivered":
        return "bg-green-100 text-green-800";
      case "shipped":
        return "bg-blue-100 text-blue-800";
      case "processing":
        return "bg-blue-100 text-blue-800";
      case "pending":
        return "bg-yellow-100 text-yellow-800";
      case "cancelled":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="space-y-6">
      {/* Stats Cards */}
      <div className="grid md:grid-cols-3 gap-4">
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Total Orders</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats.totalOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-primary-100 rounded-full flex items-center justify-center">
              <ShoppingBag className="w-6 h-6 text-primary-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">In Progress</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats.pendingOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center">
              <Clock className="w-6 h-6 text-blue-600" />
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between">
            <div>
              <p className="text-sm text-gray-600">Completed</p>
              <p className="text-3xl font-bold text-gray-900 mt-1">
                {stats.completedOrders}
              </p>
            </div>
            <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-6 h-6 text-green-600" />
            </div>
          </div>
        </div>
      </div>

      {/* Account Information */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">
          Account Information
        </h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div>
            <p className="text-sm text-gray-600">Name</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {customer?.first_name} {customer?.last_name}
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-600">Email</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {customer?.email}
            </p>
          </div>
          {customer?.phone && (
            <div>
              <p className="text-sm text-gray-600">Phone</p>
              <p className="text-base font-medium text-gray-900 mt-1">
                {customer?.phone}
              </p>
            </div>
          )}
          <div>
            <p className="text-sm text-gray-600">Account Since</p>
            <p className="text-base font-medium text-gray-900 mt-1">
              {customer?.created_at ? formatDate(customer.created_at) : "N/A"}
            </p>
          </div>
        </div>
        <div className="mt-6">
          <Link
            href="/account/profile"
            className="text-primary-600 hover:text-primary-700 font-medium text-sm"
          >
            Edit Profile →
          </Link>
        </div>
      </div>

      {/* Recent Orders */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-bold text-gray-900">Recent Orders</h2>
          <Link
            href="/account/orders"
            className="text-primary-600 hover:text-primary-700 font-medium text-sm flex items-center gap-1"
          >
            View All
            <ArrowRight className="w-4 h-4" />
          </Link>
        </div>

        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
          </div>
        ) : recentOrders.length === 0 ? (
          <div className="text-center py-12">
            <Package className="w-16 h-16 text-gray-300 mx-auto mb-4" />
            <p className="text-gray-600 mb-4">
              You haven't placed any orders yet
            </p>
            <Link
              href="/products"
              className="inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-semibold hover:bg-primary-700"
            >
              Start Shopping
              <ArrowRight className="w-5 h-5" />
            </Link>
          </div>
        ) : (
          <div className="space-y-4">
            {recentOrders.map((order) => (
              <Link
                key={order.id}
                href={`/account/orders/${order.id}`}
                className="block border border-gray-200 rounded-lg p-4 hover:border-primary-300 hover:bg-primary-50 transition-colors"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
                      <Package className="w-5 h-5 text-primary-600" />
                    </div>
                    <div>
                      <p className="font-medium text-gray-900">
                        Order #{order.order_number}
                      </p>
                      <p className="text-sm text-gray-600">
                        {formatDate(order.created_at)}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-bold text-gray-900">
                      {formatPrice(order.total)}
                    </p>
                    <span
                      className={`inline-block px-2 py-1 text-xs font-medium rounded-full capitalize ${getStatusColor(
                        order.status,
                      )}`}
                    >
                      {order.status}
                    </span>
                  </div>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <p className="text-gray-600">
                    {order.items.length}{" "}
                    {order.items.length === 1 ? "item" : "items"}
                  </p>
                  <span className="text-primary-600 font-medium">
                    View Details →
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
