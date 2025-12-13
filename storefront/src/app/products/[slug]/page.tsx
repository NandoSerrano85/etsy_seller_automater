"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { ShoppingCart, Check, X } from "lucide-react";
import { productsApi } from "@/lib/api";
import { Product, ProductVariant } from "@/types";
import {
  formatPrice,
  formatPrintMethod,
  formatCategory,
  getImageUrl,
} from "@/lib/utils";
import { useStore } from "@/store/useStore";
import toast from "react-hot-toast";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const { addToCart } = useStore();

  const [product, setProduct] = useState<Product | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(
    null,
  );
  const [quantity, setQuantity] = useState(1);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [isAddingToCart, setIsAddingToCart] = useState(false);

  useEffect(() => {
    fetchProduct();
  }, [slug]);

  const fetchProduct = async () => {
    setIsLoading(true);
    try {
      const data = await productsApi.getBySlug(slug);
      setProduct(data);

      // Select first variant if available
      if (data.variants && data.variants.length > 0) {
        setSelectedVariant(data.variants[0]);
      }
    } catch (error) {
      console.error("Failed to fetch product:", error);
      toast.error("Product not found");
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddToCart = async () => {
    if (!product) return;

    setIsAddingToCart(true);
    try {
      await addToCart(product.id, quantity, selectedVariant?.id);
      toast.success("Added to cart!");
    } catch (error) {
      toast.error("Failed to add to cart");
    } finally {
      setIsAddingToCart(false);
    }
  };

  const handleQuantityChange = (delta: number) => {
    setQuantity((prev) => Math.max(1, prev + delta));
  };

  if (isLoading) {
    return (
      <div className="container py-12">
        <div className="flex justify-center items-center min-h-screen">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
        </div>
      </div>
    );
  }

  if (!product) {
    return (
      <div className="container py-12">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900 mb-4">
            Product not found
          </h1>
          <p className="text-gray-600">
            The product you're looking for doesn't exist or has been removed.
          </p>
        </div>
      </div>
    );
  }

  // Calculate available quantity
  const availableQuantity = selectedVariant
    ? selectedVariant.inventory_quantity
    : product.inventory_quantity;

  const isOutOfStock =
    product.track_inventory &&
    availableQuantity <= 0 &&
    !product.allow_backorder;

  // Get images
  const images =
    product.image_gallery && product.image_gallery.length > 0
      ? product.image_gallery
      : product.image_url
        ? [product.image_url]
        : [];

  const currentImage =
    images[selectedImageIndex] || "/images/placeholder-product.jpg";

  return (
    <div className="bg-white">
      <div className="container py-8">
        {/* Breadcrumb */}
        <nav className="flex mb-8 text-sm">
          <a href="/" className="text-gray-500 hover:text-gray-700">
            Home
          </a>
          <span className="mx-2 text-gray-400">/</span>
          <a href="/products" className="text-gray-500 hover:text-gray-700">
            Products
          </a>
          <span className="mx-2 text-gray-400">/</span>
          <span className="text-gray-900">{product.name}</span>
        </nav>

        <div className="lg:grid lg:grid-cols-2 lg:gap-12">
          {/* Images */}
          <div>
            {/* Main Image */}
            <div className="aspect-square bg-gray-100 rounded-lg overflow-hidden mb-4">
              <img
                src={getImageUrl(currentImage)}
                alt={product.name}
                className="w-full h-full object-cover"
              />
            </div>

            {/* Thumbnail Gallery */}
            {images.length > 1 && (
              <div className="grid grid-cols-4 gap-2">
                {images.map((image, index) => (
                  <button
                    key={index}
                    onClick={() => setSelectedImageIndex(index)}
                    className={`aspect-square bg-gray-100 rounded-lg overflow-hidden border-2 ${
                      selectedImageIndex === index
                        ? "border-primary-600"
                        : "border-transparent"
                    }`}
                  >
                    <img
                      src={getImageUrl(image)}
                      alt={`${product.name} ${index + 1}`}
                      className="w-full h-full object-cover"
                    />
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Product Info */}
          <div>
            {/* Badges */}
            <div className="flex gap-2 mb-4">
              {product.is_featured && (
                <span className="px-3 py-1 bg-primary-600 text-white text-sm rounded-full">
                  Featured
                </span>
              )}
              {product.compare_at_price &&
                product.compare_at_price > product.price && (
                  <span className="px-3 py-1 bg-red-600 text-white text-sm rounded-full">
                    Sale
                  </span>
                )}
            </div>

            {/* Title */}
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              {product.name}
            </h1>

            {/* Category & Print Method */}
            <div className="flex gap-4 text-sm text-gray-600 mb-4">
              <span>{formatPrintMethod(product.print_method)}</span>
              <span>•</span>
              <span>{formatCategory(product.category)}</span>
              {product.sku && (
                <>
                  <span>•</span>
                  <span>SKU: {product.sku}</span>
                </>
              )}
            </div>

            {/* Price */}
            <div className="mb-6">
              <div className="flex items-center gap-3">
                <span className="text-3xl font-bold text-gray-900">
                  {formatPrice(selectedVariant?.price || product.price)}
                </span>
                {product.compare_at_price &&
                  product.compare_at_price > product.price && (
                    <span className="text-xl text-gray-500 line-through">
                      {formatPrice(product.compare_at_price)}
                    </span>
                  )}
              </div>
            </div>

            {/* Short Description */}
            {product.short_description && (
              <p className="text-gray-600 mb-6">{product.short_description}</p>
            )}

            {/* Variants */}
            {product.variants && product.variants.length > 0 && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-900 mb-3">
                  {product.variants[0].option_name || "Options"}
                </label>
                <div className="flex flex-wrap gap-2">
                  {product.variants.map((variant) => (
                    <button
                      key={variant.id}
                      onClick={() => setSelectedVariant(variant)}
                      className={`px-4 py-2 border-2 rounded-lg font-medium ${
                        selectedVariant?.id === variant.id
                          ? "border-primary-600 bg-primary-50 text-primary-700"
                          : "border-gray-300 hover:border-gray-400"
                      }`}
                    >
                      {variant.option_value || variant.name}
                    </button>
                  ))}
                </div>
              </div>
            )}

            {/* Stock Status */}
            <div className="mb-6">
              {isOutOfStock ? (
                <div className="flex items-center gap-2 text-red-600">
                  <X className="w-5 h-5" />
                  <span className="font-medium">Out of Stock</span>
                </div>
              ) : product.track_inventory ? (
                <div className="flex items-center gap-2 text-green-600">
                  <Check className="w-5 h-5" />
                  <span className="font-medium">
                    {availableQuantity} in stock
                  </span>
                </div>
              ) : (
                <div className="flex items-center gap-2 text-green-600">
                  <Check className="w-5 h-5" />
                  <span className="font-medium">In Stock</span>
                </div>
              )}
            </div>

            {/* Quantity Selector */}
            {!isOutOfStock && (
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-900 mb-3">
                  Quantity
                </label>
                <div className="flex items-center gap-3">
                  <button
                    onClick={() => handleQuantityChange(-1)}
                    disabled={quantity <= 1}
                    className="w-10 h-10 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    -
                  </button>
                  <span className="text-lg font-medium w-12 text-center">
                    {quantity}
                  </span>
                  <button
                    onClick={() => handleQuantityChange(1)}
                    disabled={
                      product.track_inventory && quantity >= availableQuantity
                    }
                    className="w-10 h-10 rounded-lg border border-gray-300 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    +
                  </button>
                </div>
              </div>
            )}

            {/* Add to Cart Button */}
            <button
              onClick={handleAddToCart}
              disabled={isOutOfStock || isAddingToCart}
              className="w-full flex items-center justify-center gap-2 bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed mb-4"
            >
              <ShoppingCart className="w-5 h-5" />
              {isAddingToCart
                ? "Adding..."
                : isOutOfStock
                  ? "Out of Stock"
                  : "Add to Cart"}
            </button>

            {/* Backorder Notice */}
            {product.allow_backorder &&
              product.track_inventory &&
              availableQuantity <= 0 && (
                <p className="text-sm text-yellow-600 mb-4">
                  This item is currently on backorder. Order now and we'll ship
                  when available.
                </p>
              )}

            {/* Long Description */}
            {product.long_description && (
              <div className="mt-8 border-t pt-8">
                <h2 className="text-xl font-bold text-gray-900 mb-4">
                  Product Details
                </h2>
                <div className="prose prose-sm max-w-none text-gray-600">
                  {product.long_description}
                </div>
              </div>
            )}

            {/* Product Info */}
            <div className="mt-8 border-t pt-8">
              <h2 className="text-xl font-bold text-gray-900 mb-4">
                Information
              </h2>
              <dl className="space-y-3">
                <div className="flex justify-between">
                  <dt className="text-gray-600">Type:</dt>
                  <dd className="font-medium text-gray-900">
                    {product.product_type === "digital"
                      ? "Digital Download"
                      : "Physical Product"}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Print Method:</dt>
                  <dd className="font-medium text-gray-900">
                    {formatPrintMethod(product.print_method)}
                  </dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-gray-600">Category:</dt>
                  <dd className="font-medium text-gray-900">
                    {formatCategory(product.category)}
                  </dd>
                </div>
              </dl>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
