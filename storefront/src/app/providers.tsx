"use client";

import { useEffect } from "react";
import { useStore } from "@/store/useStore";
import { customerApi } from "@/lib/api";
import { BrandingProvider } from "@/contexts/BrandingContext";

export function Providers({ children }: { children: React.ReactNode }) {
  const { setCustomer, fetchCart } = useStore();

  useEffect(() => {
    // Initialize auth state from localStorage
    const customer = customerApi.getCurrentCustomer();
    if (customer) {
      setCustomer(customer);
    }

    // Fetch cart on mount
    fetchCart();
  }, [setCustomer, fetchCart]);

  return <BrandingProvider>{children}</BrandingProvider>;
}
