"use client";

import Link from "next/link";

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 to-teal-50">
      {/* Header */}
      <header className="py-6 px-4">
        <div className="container mx-auto flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-10 h-10 bg-emerald-600 rounded-lg flex items-center justify-center">
              <svg
                className="w-6 h-6 text-white"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M13 10V3L4 14h7v7l9-11h-7z"
                />
              </svg>
            </div>
            <span className="text-xl font-bold text-gray-900">CraftFlow</span>
          </div>
          <a
            href="https://craftflow.store"
            className="text-emerald-600 hover:text-emerald-700 font-medium"
          >
            Go to CraftFlow
          </a>
        </div>
      </header>

      {/* Hero Section */}
      <main className="container mx-auto px-4 py-20">
        <div className="max-w-3xl mx-auto text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-6">
            CraftFlow Storefronts
          </h1>
          <p className="text-xl text-gray-600 mb-12">
            This is the multi-tenant storefront platform for CraftFlow sellers.
            Each seller has their own unique store URL.
          </p>

          {/* Example Stores */}
          <div className="bg-white rounded-2xl shadow-lg p-8 mb-12">
            <h2 className="text-lg font-semibold text-gray-900 mb-4">
              How it works
            </h2>
            <div className="text-left space-y-4">
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-emerald-600 font-bold">1</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    Sellers create their store
                  </p>
                  <p className="text-gray-600 text-sm">
                    Using the CraftFlow admin panel at craftflow.store
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-emerald-600 font-bold">2</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">
                    Choose a unique store URL
                  </p>
                  <p className="text-gray-600 text-sm">
                    Like{" "}
                    <code className="bg-gray-100 px-1 rounded">
                      /store/myshop
                    </code>
                  </p>
                </div>
              </div>
              <div className="flex items-start space-x-3">
                <div className="w-8 h-8 bg-emerald-100 rounded-full flex items-center justify-center flex-shrink-0">
                  <span className="text-emerald-600 font-bold">3</span>
                </div>
                <div>
                  <p className="font-medium text-gray-900">Start selling!</p>
                  <p className="text-gray-600 text-sm">
                    Customers can browse and purchase from the unique store URL
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* CTA */}
          <div className="space-y-4">
            <p className="text-gray-600">Looking to create your own store?</p>
            <a
              href="https://craftflow.store"
              className="inline-flex items-center px-8 py-4 bg-emerald-600 text-white rounded-lg font-semibold hover:bg-emerald-700 transition-colors"
            >
              Get Started with CraftFlow
              <svg
                className="ml-2 w-5 h-5"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9 5l7 7-7 7"
                />
              </svg>
            </a>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="py-8 px-4 border-t border-gray-200">
        <div className="container mx-auto text-center text-gray-600">
          <p>
            &copy; {new Date().getFullYear()} CraftFlow. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
