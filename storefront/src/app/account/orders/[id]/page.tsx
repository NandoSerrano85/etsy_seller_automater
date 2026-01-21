"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { ordersApi } from "@/lib/api";
import { Order } from "@/types";
import { formatPrice, formatDate } from "@/lib/utils";
import {
  ArrowLeft,
  Package,
  MapPin,
  CreditCard,
  Download,
  Truck,
} from "lucide-react";
import toast from "react-hot-toast";

export default function OrderDetailPage({
  params,
}: {
  params: { id: string };
}) {
  const router = useRouter();
  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchOrder();
  }, [params.id]);

  const fetchOrder = async () => {
    setIsLoading(true);
    try {
      const data = await ordersApi.getById(params.id);
      setOrder(data);
    } catch (error) {
      console.error("Failed to fetch order:", error);
      toast.error("Order not found");
      router.push("/account/orders");
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case "fulfilled":
        return "bg-green-100 text-green-800";
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

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow-sm p-12">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!order) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Back Button */}
      <Link
        href="/account/orders"
        className="inline-flex items-center gap-2 text-gray-600 hover:text-gray-900"
      >
        <ArrowLeft className="w-5 h-5" />
        Back to Orders
      </Link>

      {/* Order Header */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-4">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              Order #{order.order_number}
            </h1>
            <p className="text-gray-600 mt-1">
              Placed on {formatDate(order.created_at)}
            </p>
          </div>
          <span
            className={`inline-block px-4 py-2 text-sm font-medium rounded-full capitalize ${getStatusColor(
              order.fulfillment_status,
            )}`}
          >
            {order.fulfillment_status}
          </span>
        </div>

        {/* Order Progress */}
        {order.status !== "cancelled" && (
          <div className="mt-6">
            <div className="flex items-center justify-between">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    order.payment_status === "paid"
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <CreditCard className="w-5 h-5" />
                </div>
                <p className="text-xs mt-2 text-gray-600">Payment</p>
              </div>

              <div className="flex-1 h-1 bg-gray-200">
                <div
                  className={`h-full transition-all ${
                    order.status === "processing" ||
                    order.status === "shipped" ||
                    order.status === "delivered"
                      ? "bg-green-600"
                      : "bg-gray-200"
                  }`}
                />
              </div>

              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    order.status === "processing" ||
                    order.status === "shipped" ||
                    order.status === "delivered"
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <Package className="w-5 h-5" />
                </div>
                <p className="text-xs mt-2 text-gray-600">Processing</p>
              </div>

              <div className="flex-1 h-1 bg-gray-200">
                <div
                  className={`h-full transition-all ${
                    order.status === "shipped" || order.status === "delivered"
                      ? "bg-green-600"
                      : "bg-gray-200"
                  }`}
                />
              </div>

              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-10 h-10 rounded-full flex items-center justify-center ${
                    order.status === "delivered"
                      ? "bg-green-600 text-white"
                      : "bg-gray-200 text-gray-600"
                  }`}
                >
                  <Truck className="w-5 h-5" />
                </div>
                <p className="text-xs mt-2 text-gray-600">Delivered</p>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Order Items */}
      <div className="bg-white rounded-lg shadow-sm p-6">
        <h2 className="text-lg font-bold text-gray-900 mb-4">Order Items</h2>
        <div className="space-y-4">
          {order.items.map((item, index) => (
            <div
              key={index}
              className="flex gap-4 pb-4 border-b last:border-b-0"
            >
              <div className="flex-1">
                <p className="font-medium text-gray-900">{item.product_name}</p>
                {item.variant_name && (
                  <p className="text-sm text-gray-500">{item.variant_name}</p>
                )}
                <p className="text-sm text-gray-600 mt-1">
                  Quantity: {item.quantity}
                </p>
                {item.digital_file_url && (
                  <a
                    href={item.digital_file_url}
                    download
                    className="inline-flex items-center gap-2 text-sm text-primary-600 hover:text-primary-700 mt-2"
                  >
                    <Download className="w-4 h-4" />
                    Download Digital File
                  </a>
                )}
              </div>
              <div className="text-right">
                <p className="font-medium text-gray-900">
                  {formatPrice(item.total)}
                </p>
                <p className="text-sm text-gray-500">
                  {formatPrice(item.price)} each
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Order Summary */}
        <div className="border-t border-gray-200 pt-4 mt-4 space-y-2">
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Subtotal:</span>
            <span className="text-gray-900">{formatPrice(order.subtotal)}</span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Shipping:</span>
            <span className="text-gray-900">
              {order.shipping === 0 ? "FREE" : formatPrice(order.shipping)}
            </span>
          </div>
          <div className="flex justify-between text-sm">
            <span className="text-gray-600">Tax:</span>
            <span className="text-gray-900">{formatPrice(order.tax)}</span>
          </div>
          <div className="flex justify-between text-lg font-bold border-t border-gray-200 pt-2 mt-2">
            <span>Total:</span>
            <span>{formatPrice(order.total)}</span>
          </div>
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Shipping Address */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-bold text-gray-900">
              Shipping Address
            </h2>
          </div>
          <div className="text-gray-600 text-sm">
            <p className="font-medium text-gray-900">
              {order.shipping_address.first_name}{" "}
              {order.shipping_address.last_name}
            </p>
            <p>{order.shipping_address.address1}</p>
            {order.shipping_address.address2 && (
              <p>{order.shipping_address.address2}</p>
            )}
            <p>
              {order.shipping_address.city}, {order.shipping_address.state}{" "}
              {order.shipping_address.zip_code}
            </p>
            <p>{order.shipping_address.country}</p>
            {order.shipping_address.phone && (
              <p className="mt-2">Phone: {order.shipping_address.phone}</p>
            )}
          </div>
        </div>

        {/* Payment Information */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center gap-2 mb-4">
            <CreditCard className="w-5 h-5 text-gray-600" />
            <h2 className="text-lg font-bold text-gray-900">
              Payment Information
            </h2>
          </div>
          <div className="text-sm space-y-2">
            <div>
              <span className="text-gray-600">Payment Status:</span>
              <span className="ml-2 font-medium capitalize">
                {order.payment_status}
              </span>
            </div>
            {order.payment_intent_id && (
              <div>
                <span className="text-gray-600">Transaction ID:</span>
                <span className="ml-2 font-mono text-xs">
                  {order.payment_intent_id}
                </span>
              </div>
            )}
            {order.tracking_number && (
              <div>
                <span className="text-gray-600">Tracking Number:</span>
                <span className="ml-2 font-medium">
                  {order.tracking_number}
                </span>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Need Help */}
      <div className="bg-primary-50 rounded-lg p-6 text-center">
        <p className="text-gray-700 mb-2">Need help with your order?</p>
        <Link
          href="/contact"
          className="text-primary-600 hover:text-primary-700 font-medium"
        >
          Contact Support →
        </Link>
      </div>
    </div>
  );
}
