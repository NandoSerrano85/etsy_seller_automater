import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Cart, Customer } from '@/types';
import { cartApi, customerApi } from '@/lib/api';

interface StoreState {
  // Cart state
  cart: Cart | null;
  isLoadingCart: boolean;
  fetchCart: () => Promise<void>;
  addToCart: (productId: string, quantity: number, variantId?: string) => Promise<void>;
  updateCartItem: (itemId: string, quantity: number) => Promise<void>;
  removeFromCart: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;

  // Auth state
  customer: Customer | null;
  isAuthenticated: boolean;
  setCustomer: (customer: Customer | null) => void;
  logout: () => void;

  // UI state
  isMobileMenuOpen: boolean;
  setMobileMenuOpen: (open: boolean) => void;
  isCartOpen: boolean;
  setCartOpen: (open: boolean) => void;
}

export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      // Cart state
      cart: null,
      isLoadingCart: false,

      fetchCart: async () => {
        set({ isLoadingCart: true });
        try {
          const cart = await cartApi.get();
          set({ cart, isLoadingCart: false });
        } catch (error) {
          console.error('Failed to fetch cart:', error);
          set({ isLoadingCart: false });
        }
      },

      addToCart: async (productId: string, quantity: number, variantId?: string) => {
        set({ isLoadingCart: true });
        try {
          const cart = await cartApi.add(productId, quantity, variantId);
          set({ cart, isLoadingCart: false, isCartOpen: true });
        } catch (error) {
          console.error('Failed to add to cart:', error);
          set({ isLoadingCart: false });
          throw error;
        }
      },

      updateCartItem: async (itemId: string, quantity: number) => {
        set({ isLoadingCart: true });
        try {
          const cart = await cartApi.update(itemId, quantity);
          set({ cart, isLoadingCart: false });
        } catch (error) {
          console.error('Failed to update cart:', error);
          set({ isLoadingCart: false });
          throw error;
        }
      },

      removeFromCart: async (itemId: string) => {
        set({ isLoadingCart: true });
        try {
          await cartApi.remove(itemId);
          await get().fetchCart();
        } catch (error) {
          console.error('Failed to remove from cart:', error);
          set({ isLoadingCart: false });
          throw error;
        }
      },

      clearCart: async () => {
        set({ isLoadingCart: true });
        try {
          await cartApi.clear();
          set({ cart: null, isLoadingCart: false });
        } catch (error) {
          console.error('Failed to clear cart:', error);
          set({ isLoadingCart: false });
          throw error;
        }
      },

      // Auth state
      customer: null,
      isAuthenticated: false,

      setCustomer: (customer: Customer | null) => {
        set({ customer, isAuthenticated: !!customer });
      },

      logout: () => {
        customerApi.logout();
        set({ customer: null, isAuthenticated: false, cart: null });
      },

      // UI state
      isMobileMenuOpen: false,
      setMobileMenuOpen: (open: boolean) => set({ isMobileMenuOpen: open }),
      isCartOpen: false,
      setCartOpen: (open: boolean) => set({ isCartOpen: open }),
    }),
    {
      name: 'ecommerce-storage',
      partialize: (state) => ({
        customer: state.customer,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
