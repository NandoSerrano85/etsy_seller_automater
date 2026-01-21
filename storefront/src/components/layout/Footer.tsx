"use client";

import Link from "next/link";
import { useBranding } from "@/contexts/BrandingContext";

export function Footer() {
  const currentYear = new Date().getFullYear();
  const { settings } = useBranding();

  return (
    <footer className="bg-gray-900 text-gray-300">
      <div className="container py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Company Info */}
          <div>
            <h3 className="text-white text-lg font-bold mb-4">
              {settings.store_name}
            </h3>
            <p className="text-sm">{settings.store_description}</p>
          </div>

          {/* Shop */}
          <div>
            <h4 className="text-white font-semibold mb-4">Shop</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/products"
                  className="hover:text-white transition-colors"
                >
                  All Products
                </Link>
              </li>
              <li>
                <Link
                  href="/products?print_method=uvdtf"
                  className="hover:text-white transition-colors"
                >
                  UVDTF Transfers
                </Link>
              </li>
              <li>
                <Link
                  href="/products?print_method=dtf"
                  className="hover:text-white transition-colors"
                >
                  DTF Transfers
                </Link>
              </li>
              <li>
                <Link
                  href="/products?print_method=sublimation"
                  className="hover:text-white transition-colors"
                >
                  Sublimation
                </Link>
              </li>
            </ul>
          </div>

          {/* Customer Service */}
          <div>
            <h4 className="text-white font-semibold mb-4">Customer Service</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/account"
                  className="hover:text-white transition-colors"
                >
                  My Account
                </Link>
              </li>
              <li>
                <Link
                  href="/track-order"
                  className="hover:text-white transition-colors"
                >
                  Track Order
                </Link>
              </li>
              <li>
                <Link
                  href="/shipping"
                  className="hover:text-white transition-colors"
                >
                  Shipping Info
                </Link>
              </li>
              <li>
                <Link
                  href="/returns"
                  className="hover:text-white transition-colors"
                >
                  Returns
                </Link>
              </li>
            </ul>
          </div>

          {/* About */}
          <div>
            <h4 className="text-white font-semibold mb-4">About</h4>
            <ul className="space-y-2 text-sm">
              <li>
                <Link
                  href="/about"
                  className="hover:text-white transition-colors"
                >
                  About Us
                </Link>
              </li>
              <li>
                <Link
                  href="/contact"
                  className="hover:text-white transition-colors"
                >
                  Contact
                </Link>
              </li>
              <li>
                <Link
                  href="/privacy"
                  className="hover:text-white transition-colors"
                >
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link
                  href="/terms"
                  className="hover:text-white transition-colors"
                >
                  Terms of Service
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="border-t border-gray-800 mt-8 pt-8 text-sm text-center">
          <p>
            &copy; {currentYear} {settings.store_name}. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
