"use client";

import { useEffect, useState } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle, Package, Mail, ArrowRight } from "lucide-react";
import { ordersApi } from "@/lib/api";
import { Order } from "@/types";
import { formatPrice, formatDate } from "@/lib/utils";

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const orderNumber = searchParams.get("order_number");

  const [order, setOrder] = useState<Order | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    if (!orderNumber) {
      router.push("/");
      return;
    }

    fetchOrder();
  }, [orderNumber]);

  const fetchOrder = async () => {
    if (!orderNumber) return;

    setIsLoading(true);
    try {
      const data = await ordersApi.getByNumber(orderNumber);
      setOrder(data);
    } catch (error) {
      console.error("Failed to fetch order:", error);
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (!order) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Order not found
          </h1>
          <Link href="/" className="text-primary-600 hover:text-primary-700">
            Return to homepage
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container max-w-3xl">
        {/* Success Message */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6 text-center">
          <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
            <CheckCircle className="w-10 h-10 text-green-600" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Order Confirmed!
          </h1>
          <p className="text-gray-600 mb-4">
            Thank you for your purchase. Your order has been received and is
            being processed.
          </p>
          <div className="bg-gray-50 rounded-lg p-4 inline-block">
            <p className="text-sm text-gray-600 mb-1">Order Number</p>
            <p className="text-2xl font-bold text-primary-600">
              {order.order_number}
            </p>
          </div>
        </div>

        {/* Order Details */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <h2 className="text-xl font-bold mb-4">Order Details</h2>

          {/* Order Items */}
          <div className="space-y-4 mb-6">
            {order.items.map((item, index) => (
              <div
                key={index}
                className="flex gap-4 pb-4 border-b last:border-b-0"
              >
                <div className="flex-1">
                  <p className="font-medium">{item.product_name}</p>
                  {item.variant_name && (
                    <p className="text-sm text-gray-500">{item.variant_name}</p>
                  )}
                  <p className="text-sm text-gray-600">
                    Quantity: {item.quantity}
                  </p>
                </div>
                <div className="text-right">
                  <p className="font-medium">{formatPrice(item.total)}</p>
                  <p className="text-sm text-gray-500">
                    {formatPrice(item.price)} each
                  </p>
                </div>
              </div>
            ))}
          </div>

          {/* Order Summary */}
          <div className="border-t pt-4 space-y-2">
            <div className="flex justify-between text-sm">
              <span>Subtotal:</span>
              <span>{formatPrice(order.subtotal)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Shipping:</span>
              <span>
                {order.shipping === 0 ? "FREE" : formatPrice(order.shipping)}
              </span>
            </div>
            <div className="flex justify-between text-sm">
              <span>Tax:</span>
              <span>{formatPrice(order.tax)}</span>
            </div>
            <div className="flex justify-between text-lg font-bold border-t pt-2">
              <span>Total:</span>
              <span>{formatPrice(order.total)}</span>
            </div>
          </div>
        </div>

        {/* Shipping Information */}
        <div className="bg-white rounded-lg shadow-sm p-8 mb-6">
          <h2 className="text-xl font-bold mb-4">Shipping Information</h2>
          <div className="grid md:grid-cols-2 gap-6">
            <div>
              <h3 className="font-medium text-gray-900 mb-2">
                Shipping Address
              </h3>
              <div className="text-gray-600 text-sm">
                <p>
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

            <div>
              <h3 className="font-medium text-gray-900 mb-2">
                Order Information
              </h3>
              <div className="text-gray-600 text-sm space-y-1">
                <p>
                  <span className="font-medium">Order Date:</span>{" "}
                  {formatDate(order.created_at)}
                </p>
                <p>
                  <span className="font-medium">Payment Status:</span>{" "}
                  <span className="capitalize">{order.payment_status}</span>
                </p>
                <p>
                  <span className="font-medium">Fulfillment:</span>{" "}
                  <span className="capitalize">{order.fulfillment_status}</span>
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* What's Next */}
        <div className="bg-primary-50 rounded-lg p-6 mb-6">
          <h2 className="text-lg font-bold text-primary-900 mb-4">
            What happens next?
          </h2>
          <div className="space-y-3">
            <div className="flex gap-3">
              <Mail className="w-6 h-6 text-primary-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-primary-900">
                  Order Confirmation Email
                </p>
                <p className="text-sm text-primary-700">
                  We've sent a confirmation email to{" "}
                  {order.customer_id ? "your email address" : order.guest_email}
                </p>
              </div>
            </div>
            <div className="flex gap-3">
              <Package className="w-6 h-6 text-primary-600 flex-shrink-0" />
              <div>
                <p className="font-medium text-primary-900">Order Processing</p>
                <p className="text-sm text-primary-700">
                  We'll prepare your order and send you tracking information
                  once it ships
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex gap-4">
          {order.customer_id ? (
            <Link
              href="/account/orders"
              className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 text-center flex items-center justify-center gap-2"
            >
              View All Orders
              <ArrowRight className="w-5 h-5" />
            </Link>
          ) : (
            <Link
              href={`/track-order?order_number=${order.order_number}`}
              className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 text-center flex items-center justify-center gap-2"
            >
              Track Order
              <ArrowRight className="w-5 h-5" />
            </Link>
          )}
          <Link
            href="/products"
            className="flex-1 bg-gray-200 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:bg-gray-300 text-center"
          >
            Continue Shopping
          </Link>
        </div>

        {/* Customer Support */}
        <div className="mt-8 text-center text-sm text-gray-600">
          <p>
            Need help with your order?{" "}
            <Link
              href="/contact"
              className="text-primary-600 hover:text-primary-700"
            >
              Contact Support
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
