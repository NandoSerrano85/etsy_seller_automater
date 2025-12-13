// Product Types
export type PrintMethod =
  | "uvdtf"
  | "dtf"
  | "sublimation"
  | "vinyl"
  | "other"
  | "digital";
export type ProductCategory =
  | "cup_wraps"
  | "single_square"
  | "single_rectangle"
  | "other";
export type ProductType = "physical" | "digital";

export interface ProductVariant {
  id: string;
  product_id: string;
  name: string;
  sku?: string;
  price?: number;
  inventory_quantity: number;
  option_name?: string;
  option_value?: string;
}

export interface Product {
  id: string;
  name: string;
  slug: string;
  product_type: ProductType;
  print_method: PrintMethod;
  category: ProductCategory;
  short_description?: string;
  long_description?: string;
  price: number;
  compare_at_price?: number;
  sku?: string;
  image_url?: string;
  image_gallery?: string[];
  is_active: boolean;
  is_featured: boolean;
  track_inventory: boolean;
  inventory_quantity: number;
  allow_backorder: boolean;
  design_id?: string;
  variants?: ProductVariant[];
  created_at: string;
  updated_at: string;
}

// Cart Types
export interface CartItem {
  product_id: string;
  variant_id?: string;
  product_name: string;
  variant_name?: string;
  sku?: string;
  price: number;
  quantity: number;
  subtotal: number;
  image_url?: string;
}

export interface Cart {
  id: string;
  session_id?: string;
  customer_id?: string;
  items: CartItem[];
  subtotal: number;
  is_active: boolean;
  expires_at: string;
  created_at: string;
  updated_at: string;
}

// Customer Types
export interface Customer {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  accepts_marketing: boolean;
  email_verified: boolean;
  total_spent: number;
  order_count: number;
  created_at: string;
}

export interface CustomerAddress {
  id: string;
  customer_id: string;
  first_name: string;
  last_name: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  phone?: string;
  is_default_shipping: boolean;
  is_default_billing: boolean;
}

// Alias for address management pages
export interface Address {
  id: number;
  customer_id?: string;
  first_name: string;
  last_name: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  phone?: string;
  is_default: boolean;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  customer: Customer;
}

// Order Types
export type OrderStatus =
  | "pending"
  | "processing"
  | "shipped"
  | "delivered"
  | "cancelled";
export type PaymentStatus = "pending" | "paid" | "failed" | "refunded";
export type FulfillmentStatus =
  | "unfulfilled"
  | "fulfilled"
  | "partially_fulfilled";

export interface OrderItem {
  id: string;
  order_id: string;
  product_id?: string;
  variant_id?: string;
  product_name: string;
  variant_name?: string;
  sku?: string;
  price: number;
  quantity: number;
  total: number;
}

export interface Order {
  id: string;
  order_number: string;
  customer_id?: string;
  guest_email?: string;
  subtotal: number;
  tax: number;
  shipping: number;
  discount: number;
  total: number;
  shipping_address: CustomerAddress;
  billing_address: CustomerAddress;
  payment_status: PaymentStatus;
  payment_method: string;
  payment_id?: string;
  fulfillment_status: FulfillmentStatus;
  tracking_number?: string;
  customer_note?: string;
  status: OrderStatus;
  items: OrderItem[];
  created_at: string;
  updated_at: string;
}

// Checkout Types
export interface CheckoutAddress {
  first_name: string;
  last_name: string;
  company?: string;
  address1: string;
  address2?: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  phone?: string;
}

export interface CheckoutInit {
  shipping_address: CheckoutAddress;
  billing_address?: CheckoutAddress;
  customer_note?: string;
  guest_email?: string;
}

export interface CheckoutResponse {
  session_id: string;
  cart_id: string;
  subtotal: number;
  tax: number;
  shipping: number;
  total: number;
  shipping_address: CheckoutAddress;
  billing_address: CheckoutAddress;
}

export interface PaymentIntentResponse {
  client_secret: string;
  payment_intent_id: string;
}

// API Response Types
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export interface ApiError {
  detail: string;
  status?: number;
}
