"use client";

import { useEffect } from "react";
import { useStore as useCartStore } from "@/store/useStore";
import { customerApi } from "@/lib/api";
import { StoreProvider } from "@/contexts/StoreContext";
import { BrandingProvider } from "@/contexts/BrandingContext";

export function Providers({ children }: { children: React.ReactNode }) {
  const { setCustomer, fetchCart } = useCartStore();

  useEffect(() => {
    // Initialize auth state from localStorage
    const customer = customerApi.getCurrentCustomer();
    if (customer) {
      setCustomer(customer);
    }

    // Fetch cart on mount
    fetchCart();
  }, [setCustomer, fetchCart]);

  return (
    <StoreProvider>
      <BrandingProvider>{children}</BrandingProvider>
    </StoreProvider>
  );
}
