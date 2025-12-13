'use client';

import Link from 'next/link';
import { ShoppingCart } from 'lucide-react';
import { Product } from '@/types';
import { formatPrice, formatPrintMethod, getImageUrl } from '@/lib/utils';
import { useStore } from '@/store/useStore';
import toast from 'react-hot-toast';

interface ProductCardProps {
  product: Product;
}

export function ProductCard({ product }: ProductCardProps) {
  const { addToCart } = useStore();

  const handleAddToCart = async (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();

    try {
      await addToCart(product.id, 1);
      toast.success('Added to cart!');
    } catch (error) {
      toast.error('Failed to add to cart');
    }
  };

  const imageUrl = getImageUrl(product.image_url);
  const hasDiscount = product.compare_at_price && product.compare_at_price > product.price;

  return (
    <Link
      href={`/products/${product.slug}`}
      className="group bg-white rounded-lg shadow hover:shadow-lg transition-shadow overflow-hidden"
    >
      {/* Product Image */}
      <div className="relative aspect-square bg-gray-100 overflow-hidden">
        <img
          src={imageUrl}
          alt={product.name}
          className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300"
        />

        {/* Badges */}
        <div className="absolute top-2 left-2 flex flex-col gap-2">
          {product.is_featured && (
            <span className="bg-primary-600 text-white text-xs px-2 py-1 rounded">
              Featured
            </span>
          )}
          {hasDiscount && (
            <span className="bg-red-600 text-white text-xs px-2 py-1 rounded">
              Sale
            </span>
          )}
        </div>

        {/* Quick Add Button */}
        <button
          onClick={handleAddToCart}
          className="absolute bottom-2 right-2 bg-white p-2 rounded-full shadow-lg opacity-0 group-hover:opacity-100 transition-opacity hover:bg-primary-600 hover:text-white"
          aria-label="Add to cart"
        >
          <ShoppingCart className="w-5 h-5" />
        </button>
      </div>

      {/* Product Info */}
      <div className="p-4">
        <div className="text-xs text-gray-500 mb-1">
          {formatPrintMethod(product.print_method)}
        </div>

        <h3 className="font-semibold text-gray-900 group-hover:text-primary-600 transition-colors line-clamp-2 mb-2">
          {product.name}
        </h3>

        {product.short_description && (
          <p className="text-sm text-gray-600 line-clamp-2 mb-3">
            {product.short_description}
          </p>
        )}

        {/* Price */}
        <div className="flex items-center gap-2">
          <span className="text-lg font-bold text-gray-900">
            {formatPrice(product.price)}
          </span>
          {hasDiscount && (
            <span className="text-sm text-gray-500 line-through">
              {formatPrice(product.compare_at_price!)}
            </span>
          )}
        </div>

        {/* Stock Status */}
        {product.track_inventory && (
          <div className="mt-2">
            {product.inventory_quantity > 0 ? (
              <span className="text-xs text-green-600">
                {product.inventory_quantity} in stock
              </span>
            ) : product.allow_backorder ? (
              <span className="text-xs text-yellow-600">Available on backorder</span>
            ) : (
              <span className="text-xs text-red-600">Out of stock</span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}
