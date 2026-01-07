"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

export default function TrackOrderPage() {
  const [orderNumber, setOrderNumber] = useState("");
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      // TODO: Implement order tracking API call
      // For now, just redirect to account orders page
      router.push("/account/orders");
    } catch (err) {
      setError(
        "Could not find order. Please check your order number and email.",
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container mx-auto px-4 py-12 max-w-2xl">
      <h1 className="text-4xl font-bold mb-8 text-center">Track Your Order</h1>

      <div className="bg-white rounded-lg shadow-md p-8">
        <p className="text-gray-600 mb-6 text-center">
          Enter your order number and email address to track your order status.
        </p>

        {error && (
          <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label
              htmlFor="orderNumber"
              className="block text-sm font-medium mb-2"
            >
              Order Number *
            </label>
            <input
              type="text"
              id="orderNumber"
              required
              value={orderNumber}
              onChange={(e) => setOrderNumber(e.target.value)}
              placeholder="e.g., ORD-12345"
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-sm text-gray-500 mt-1">
              Found in your order confirmation email
            </p>
          </div>

          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-2">
              Email Address *
            </label>
            <input
              type="email"
              id="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <p className="text-sm text-gray-500 mt-1">
              The email used when placing your order
            </p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 text-white py-3 rounded-lg font-semibold hover:bg-blue-700 transition-colors disabled:bg-gray-400 disabled:cursor-not-allowed"
          >
            {loading ? "Tracking..." : "Track Order"}
          </button>
        </form>

        <div className="mt-8 pt-6 border-t border-gray-200">
          <h3 className="font-semibold mb-3">Need Help?</h3>
          <p className="text-sm text-gray-600 mb-2">
            If you're having trouble tracking your order, please{" "}
            <a href="/contact" className="text-blue-600 hover:underline">
              contact us
            </a>{" "}
            with your order number.
          </p>
          <p className="text-sm text-gray-600">
            Already have an account?{" "}
            <a href="/account/orders" className="text-blue-600 hover:underline">
              View your orders
            </a>
          </p>
        </div>
      </div>
    </div>
  );
}
