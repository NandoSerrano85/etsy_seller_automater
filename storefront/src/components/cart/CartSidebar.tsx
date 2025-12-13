'use client';

import { X, Minus, Plus, Trash2 } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { formatPrice } from '@/lib/utils';
import Link from 'next/link';
import toast from 'react-hot-toast';

export function CartSidebar() {
  const { cart, isCartOpen, setCartOpen, updateCartItem, removeFromCart, isLoadingCart } = useStore();

  const handleUpdateQuantity = async (itemId: string, currentQuantity: number, delta: number) => {
    const newQuantity = currentQuantity + delta;
    if (newQuantity < 1) return;

    try {
      await updateCartItem(itemId, newQuantity);
    } catch (error) {
      toast.error('Failed to update quantity');
    }
  };

  const handleRemove = async (itemId: string) => {
    try {
      await removeFromCart(itemId);
      toast.success('Item removed from cart');
    } catch (error) {
      toast.error('Failed to remove item');
    }
  };

  if (!isCartOpen) return null;

  const cartItems = cart?.items || [];
  const subtotal = cart?.subtotal || 0;

  return (
    <>
      {/* Overlay */}
      <div
        className="fixed inset-0 bg-black/50 z-40 transition-opacity"
        onClick={() => setCartOpen(false)}
      />

      {/* Sidebar */}
      <div className="fixed right-0 top-0 h-full w-full max-w-md bg-white shadow-2xl z-50 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-xl font-bold">Shopping Cart</h2>
          <button
            onClick={() => setCartOpen(false)}
            className="text-gray-400 hover:text-gray-600"
            aria-label="Close cart"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Cart Items */}
        <div className="flex-1 overflow-y-auto p-6">
          {cartItems.length === 0 ? (
            <div className="text-center py-12">
              <p className="text-gray-500 mb-4">Your cart is empty</p>
              <Link
                href="/products"
                onClick={() => setCartOpen(false)}
                className="text-primary-600 hover:text-primary-700 font-medium"
              >
                Continue Shopping
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {cartItems.map((item) => {
                // Extract item ID from product_id (simplified - adjust based on your cart structure)
                const itemId = `${item.product_id}${item.variant_id ? `-${item.variant_id}` : ''}`;

                return (
                  <div key={itemId} className="flex gap-4 border-b pb-4">
                    {/* Product Image */}
                    <div className="w-20 h-20 bg-gray-100 rounded flex-shrink-0">
                      {item.image_url && (
                        <img
                          src={item.image_url}
                          alt={item.product_name}
                          className="w-full h-full object-cover rounded"
                        />
                      )}
                    </div>

                    {/* Product Info */}
                    <div className="flex-1 min-w-0">
                      <h3 className="font-medium text-sm truncate">{item.product_name}</h3>
                      {item.variant_name && (
                        <p className="text-xs text-gray-500">{item.variant_name}</p>
                      )}
                      <p className="text-sm font-semibold mt-1">{formatPrice(item.price)}</p>

                      {/* Quantity Controls */}
                      <div className="flex items-center gap-2 mt-2">
                        <button
                          onClick={() => handleUpdateQuantity(itemId, item.quantity, -1)}
                          disabled={isLoadingCart || item.quantity <= 1}
                          className="p-1 rounded border hover:bg-gray-50 disabled:opacity-50"
                        >
                          <Minus className="w-3 h-3" />
                        </button>
                        <span className="text-sm w-8 text-center">{item.quantity}</span>
                        <button
                          onClick={() => handleUpdateQuantity(itemId, item.quantity, 1)}
                          disabled={isLoadingCart}
                          className="p-1 rounded border hover:bg-gray-50 disabled:opacity-50"
                        >
                          <Plus className="w-3 h-3" />
                        </button>
                        <button
                          onClick={() => handleRemove(itemId)}
                          disabled={isLoadingCart}
                          className="ml-auto p-1 text-red-500 hover:text-red-700 disabled:opacity-50"
                          aria-label="Remove item"
                        >
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </div>

                    {/* Item Total */}
                    <div className="text-right">
                      <p className="font-semibold">{formatPrice(item.subtotal)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Footer */}
        {cartItems.length > 0 && (
          <div className="border-t p-6 space-y-4">
            <div className="flex justify-between text-lg font-bold">
              <span>Subtotal:</span>
              <span>{formatPrice(subtotal)}</span>
            </div>
            <p className="text-sm text-gray-500">
              Tax and shipping calculated at checkout
            </p>
            <Link
              href="/checkout"
              onClick={() => setCartOpen(false)}
              className="block w-full bg-primary-600 text-white text-center py-3 px-4 rounded-lg font-semibold hover:bg-primary-700 transition-colors"
            >
              Proceed to Checkout
            </Link>
            <button
              onClick={() => setCartOpen(false)}
              className="block w-full text-center py-2 text-gray-600 hover:text-gray-800"
            >
              Continue Shopping
            </button>
          </div>
        )}
      </div>
    </>
  );
}
