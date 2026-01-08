"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import dynamicImport from "next/dynamic";
import { loadStripe } from "@stripe/stripe-js";
import { Elements } from "@stripe/react-stripe-js";
import { useStore } from "@/store/useStore";
import { checkoutApi } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import toast from "react-hot-toast";
import { Loader2, CheckCircle, Truck, Clock } from "lucide-react";

// Force dynamic rendering
export const dynamic = "force-dynamic";

// Initialize Stripe
const stripePromise = checkoutApi
  .getStripeConfig()
  .then((config) => loadStripe(config.stripe_public_key));

// Dynamically import PaymentForm with no SSR
const PaymentForm = dynamicImport(() => import("./PaymentForm"), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center py-12">
      <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
    </div>
  ),
});

interface ShippingFormData {
  first_name: string;
  last_name: string;
  email: string;
  phone: string;
  address1: string;
  address2: string;
  city: string;
  state: string;
  zip_code: string;
  country: string;
  use_different_billing: boolean;
}

interface ShippingRate {
  carrier: string;
  service: string;
  service_level: string;
  amount: number;
  currency: string;
  estimated_days: number | null;
  duration_terms: string;
  rate_id: string;
  is_fallback?: boolean;
}

interface ShippingStepProps {
  shippingForm: ShippingFormData;
  onShippingChange: (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => void;
  onSubmit: (e: React.FormEvent) => Promise<void>;
  isProcessing: boolean;
  isAuthenticated: boolean;
}

interface ShippingMethodStepProps {
  shippingRates: ShippingRate[];
  selectedRate: ShippingRate | null;
  onSelectRate: (rate: ShippingRate) => void;
  onBack: () => void;
  onContinue: () => void;
  isProcessing: boolean;
}

function ShippingMethodStep({
  shippingRates,
  selectedRate,
  onSelectRate,
  onBack,
  onContinue,
  isProcessing,
}: ShippingMethodStepProps) {
  return (
    <div>
      <h2 className="text-2xl font-bold mb-6">Select Shipping Method</h2>

      <div className="space-y-3 mb-6">
        {shippingRates.map((rate) => (
          <div
            key={rate.rate_id}
            onClick={() => onSelectRate(rate)}
            className={`border rounded-lg p-4 cursor-pointer transition-all ${
              selectedRate?.rate_id === rate.rate_id
                ? "border-primary-600 bg-primary-50 shadow-md"
                : "border-gray-300 hover:border-primary-300 hover:bg-gray-50"
            }`}
          >
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Truck className="w-5 h-5 text-gray-600" />
                  <span className="font-semibold text-gray-900">
                    {rate.carrier} - {rate.service}
                  </span>
                  {rate.is_fallback && (
                    <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-0.5 rounded">
                      Estimated
                    </span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <Clock className="w-4 h-4" />
                  <span>{rate.duration_terms}</span>
                  {rate.estimated_days !== null && (
                    <span className="text-gray-500">
                      ({rate.estimated_days}{" "}
                      {rate.estimated_days === 1 ? "day" : "days"})
                    </span>
                  )}
                </div>
              </div>
              <div className="text-right">
                <div className="text-lg font-bold text-gray-900">
                  {rate.amount === 0 ? "FREE" : formatPrice(rate.amount)}
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>

      {shippingRates.length === 0 && (
        <div className="text-center py-8 text-gray-500">
          <Loader2 className="w-8 h-8 animate-spin mx-auto mb-2 text-primary-600" />
          <p>Loading shipping options...</p>
        </div>
      )}

      <div className="flex gap-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 bg-gray-200 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:bg-gray-300"
        >
          Back
        </button>
        <button
          type="button"
          onClick={onContinue}
          disabled={!selectedRate || isProcessing}
          className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing...
            </>
          ) : (
            "Continue to Payment"
          )}
        </button>
      </div>
    </div>
  );
}

function ShippingStep({
  shippingForm,
  onShippingChange,
  onSubmit,
  isProcessing,
  isAuthenticated,
}: ShippingStepProps) {
  return (
    <form onSubmit={onSubmit}>
      <h2 className="text-2xl font-bold mb-6">Shipping Information</h2>

      <div className="grid grid-cols-2 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            First Name *
          </label>
          <input
            type="text"
            name="first_name"
            required
            value={shippingForm.first_name}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Last Name *
          </label>
          <input
            type="text"
            name="last_name"
            required
            value={shippingForm.last_name}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      {!isAuthenticated && (
        <div className="mb-4">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Email *
          </label>
          <input
            type="email"
            name="email"
            required
            value={shippingForm.email}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      )}

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Phone
        </label>
        <input
          type="tel"
          name="phone"
          value={shippingForm.phone}
          onChange={onShippingChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="mb-4">
        <label className="block text-sm font-medium text-gray-700 mb-1">
          Address *
        </label>
        <input
          type="text"
          name="address1"
          required
          placeholder="Street address"
          value={shippingForm.address1}
          onChange={onShippingChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="mb-4">
        <input
          type="text"
          name="address2"
          placeholder="Apartment, suite, etc. (optional)"
          value={shippingForm.address2}
          onChange={onShippingChange}
          className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
        />
      </div>

      <div className="grid grid-cols-3 gap-4 mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            City *
          </label>
          <input
            type="text"
            name="city"
            required
            value={shippingForm.city}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            State *
          </label>
          <input
            type="text"
            name="state"
            required
            placeholder="CA"
            value={shippingForm.state}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            ZIP Code *
          </label>
          <input
            type="text"
            name="zip_code"
            required
            value={shippingForm.zip_code}
            onChange={onShippingChange}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-primary-500 focus:border-primary-500"
          />
        </div>
      </div>

      <button
        type="submit"
        disabled={isProcessing}
        className="w-full bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isProcessing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Loading shipping options...
          </>
        ) : (
          "Continue to Shipping"
        )}
      </button>
    </form>
  );
}

export default function CheckoutPage() {
  const router = useRouter();
  const { cart, customer, isAuthenticated } = useStore();
  const [currentStep, setCurrentStep] = useState<
    "shipping" | "shipping_method" | "payment"
  >("shipping");
  const [clientSecret, setClientSecret] = useState<string>("");
  const [isProcessing, setIsProcessing] = useState(false);
  const [checkoutSession, setCheckoutSession] = useState<any>(null);
  const [shippingRates, setShippingRates] = useState<ShippingRate[]>([]);
  const [selectedShippingRate, setSelectedShippingRate] =
    useState<ShippingRate | null>(null);

  const [shippingForm, setShippingForm] = useState<ShippingFormData>({
    first_name: customer?.first_name || "",
    last_name: customer?.last_name || "",
    email: customer?.email || "",
    phone: customer?.phone || "",
    address1: "",
    address2: "",
    city: "",
    state: "",
    zip_code: "",
    country: "United States",
    use_different_billing: false,
  });

  // Redirect if cart is empty
  useEffect(() => {
    if (!cart || cart.items.length === 0) {
      toast.error("Your cart is empty");
      router.push("/products");
    }
  }, [cart, router]);

  const handleShippingChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setShippingForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : value,
    }));
  };

  const handleShippingSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);

    try {
      // Fetch shipping rates from Shippo
      const rates = await checkoutApi.getShippingRates({
        first_name: shippingForm.first_name,
        last_name: shippingForm.last_name,
        address1: shippingForm.address1,
        address2: shippingForm.address2 || undefined,
        city: shippingForm.city,
        state: shippingForm.state,
        zip_code: shippingForm.zip_code,
        country: shippingForm.country,
      });

      if (rates && rates.length > 0) {
        setShippingRates(rates);
        setSelectedShippingRate(rates[0]);
      } else {
        // Use fallback rates if API returns empty
        const fallbackRates = getFallbackRates();
        setShippingRates(fallbackRates);
        setSelectedShippingRate(fallbackRates[0]);
        toast.error("Using estimated shipping rates");
      }

      setCurrentStep("shipping_method");
    } catch (error: any) {
      console.error("Failed to fetch shipping rates:", error);

      // Use fallback rates on error
      const fallbackRates = getFallbackRates();
      setShippingRates(fallbackRates);
      setSelectedShippingRate(fallbackRates[0]);

      toast.error(
        "Unable to fetch real-time rates. Using estimated shipping costs.",
      );
      setCurrentStep("shipping_method");
    } finally {
      setIsProcessing(false);
    }
  };

  // Fallback shipping rates
  const getFallbackRates = () => {
    return [
      {
        carrier: "USPS",
        service: "First Class Package",
        service_level: "usps_first",
        amount: 5.99,
        currency: "USD",
        estimated_days: 3,
        duration_terms: "2-5 business days",
        rate_id: "fallback_first_class",
        is_fallback: true,
      },
      {
        carrier: "USPS",
        service: "Priority Mail",
        service_level: "usps_priority",
        amount: 9.99,
        currency: "USD",
        estimated_days: 2,
        duration_terms: "1-3 business days",
        rate_id: "fallback_priority",
        is_fallback: true,
      },
      {
        carrier: "UPS",
        service: "UPS Ground",
        service_level: "ups_ground",
        amount: 12.99,
        currency: "USD",
        estimated_days: 4,
        duration_terms: "3-5 business days",
        rate_id: "fallback_ups_ground",
        is_fallback: true,
      },
      {
        carrier: "UPS",
        service: "UPS 2nd Day Air",
        service_level: "ups_2day",
        amount: 19.99,
        currency: "USD",
        estimated_days: 2,
        duration_terms: "2 business days",
        rate_id: "fallback_ups_2day",
        is_fallback: true,
      },
      {
        carrier: "UPS",
        service: "UPS Next Day Air",
        service_level: "ups_next_day",
        amount: 29.99,
        currency: "USD",
        estimated_days: 1,
        duration_terms: "Next business day",
        rate_id: "fallback_ups_next_day",
        is_fallback: true,
      },
      {
        carrier: "USPS",
        service: "Priority Mail Express",
        service_level: "usps_express",
        amount: 24.99,
        currency: "USD",
        estimated_days: 1,
        duration_terms: "Overnight",
        rate_id: "fallback_express",
        is_fallback: true,
      },
    ];
  };

  const handleShippingMethodContinue = async () => {
    if (!selectedShippingRate) {
      toast.error("Please select a shipping method");
      return;
    }

    setIsProcessing(true);

    try {
      // Initialize checkout with backend including shipping
      const session = await checkoutApi.initialize({
        shipping_address: {
          first_name: shippingForm.first_name,
          last_name: shippingForm.last_name,
          address1: shippingForm.address1,
          address2: shippingForm.address2 || undefined,
          city: shippingForm.city,
          state: shippingForm.state,
          zip_code: shippingForm.zip_code,
          country: shippingForm.country,
          phone: shippingForm.phone || undefined,
        },
        guest_email: !isAuthenticated ? shippingForm.email : undefined,
        shipping_method: selectedShippingRate.service_level,
      });

      setCheckoutSession(session);

      // Create payment intent
      const paymentIntent = await checkoutApi.createPaymentIntent(
        session.total,
      );
      const secret = paymentIntent.client_secret;

      setClientSecret(secret);
      setCurrentStep("payment");
    } catch (error: any) {
      console.error("Checkout initialization error:", error);
      toast.error(
        error.response?.data?.detail || "Failed to initialize checkout",
      );
    } finally {
      setIsProcessing(false);
    }
  };

  if (!cart || cart.items.length === 0) {
    return null;
  }

  const subtotal = checkoutSession?.subtotal || cart.subtotal;
  const tax = checkoutSession?.tax || 0;
  const shipping =
    checkoutSession?.shipping || selectedShippingRate?.amount || 0;
  const total = checkoutSession?.total || subtotal + tax + shipping;

  return (
    <div className="min-h-screen bg-gray-50 py-12">
      <div className="container max-w-6xl">
        {/* Progress Steps */}
        <div className="mb-8">
          <div className="flex items-center justify-center">
            <div className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  currentStep === "shipping"
                    ? "bg-primary-600 text-white"
                    : "bg-green-600 text-white"
                }`}
              >
                {currentStep === "shipping" ? (
                  "1"
                ) : (
                  <CheckCircle className="w-6 h-6" />
                )}
              </div>
              <span className="ml-2 font-medium">Shipping</span>
            </div>

            <div className="w-16 h-1 mx-4 bg-gray-300">
              <div
                className={`h-full transition-all ${currentStep !== "shipping" ? "bg-green-600" : "bg-gray-300"}`}
              />
            </div>

            <div className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  currentStep === "shipping_method"
                    ? "bg-primary-600 text-white"
                    : currentStep === "payment"
                      ? "bg-green-600 text-white"
                      : "bg-gray-300 text-gray-600"
                }`}
              >
                {currentStep === "payment" ? (
                  <CheckCircle className="w-6 h-6" />
                ) : (
                  "2"
                )}
              </div>
              <span className="ml-2 font-medium">Shipping Method</span>
            </div>

            <div className="w-16 h-1 mx-4 bg-gray-300">
              <div
                className={`h-full transition-all ${currentStep === "payment" ? "bg-green-600" : "bg-gray-300"}`}
              />
            </div>

            <div className="flex items-center">
              <div
                className={`flex items-center justify-center w-10 h-10 rounded-full ${
                  currentStep === "payment"
                    ? "bg-primary-600 text-white"
                    : "bg-gray-300 text-gray-600"
                }`}
              >
                3
              </div>
              <span className="ml-2 font-medium">Payment</span>
            </div>
          </div>
        </div>

        <div className="grid lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow-sm p-6">
              {currentStep === "shipping" && (
                <ShippingStep
                  shippingForm={shippingForm}
                  onShippingChange={handleShippingChange}
                  onSubmit={handleShippingSubmit}
                  isProcessing={isProcessing}
                  isAuthenticated={isAuthenticated}
                />
              )}

              {currentStep === "shipping_method" && (
                <ShippingMethodStep
                  shippingRates={shippingRates}
                  selectedRate={selectedShippingRate}
                  onSelectRate={setSelectedShippingRate}
                  onBack={() => setCurrentStep("shipping")}
                  onContinue={handleShippingMethodContinue}
                  isProcessing={isProcessing}
                />
              )}

              {currentStep === "payment" && clientSecret && (
                <Elements
                  stripe={stripePromise}
                  options={{
                    clientSecret,
                    appearance: {
                      theme: "stripe" as const,
                    },
                  }}
                >
                  <PaymentForm
                    checkoutSession={checkoutSession}
                    shippingForm={shippingForm}
                    total={total}
                    onBack={() => setCurrentStep("shipping_method")}
                  />
                </Elements>
              )}
            </div>
          </div>

          {/* Order Summary */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-sm p-6 sticky top-24">
              <h3 className="text-lg font-bold mb-4">Order Summary</h3>

              <div className="space-y-3 mb-4">
                {cart.items.map((item, index) => (
                  <div key={index} className="flex gap-3">
                    <div className="w-16 h-16 bg-gray-100 rounded flex-shrink-0">
                      {item.image_url && (
                        <img
                          src={item.image_url}
                          alt={item.product_name}
                          className="w-full h-full object-cover rounded"
                        />
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium truncate">
                        {item.product_name}
                      </p>
                      {item.variant_name && (
                        <p className="text-xs text-gray-500">
                          {item.variant_name}
                        </p>
                      )}
                      <p className="text-sm text-gray-600">
                        Qty: {item.quantity}
                      </p>
                    </div>
                    <div className="text-sm font-medium">
                      {formatPrice(item.subtotal)}
                    </div>
                  </div>
                ))}
              </div>

              <div className="border-t pt-4 space-y-2">
                <div className="flex justify-between text-sm">
                  <span>Subtotal:</span>
                  <span>{formatPrice(subtotal)}</span>
                </div>
                {(selectedShippingRate || checkoutSession) && (
                  <>
                    <div className="flex justify-between text-sm">
                      <span>Shipping:</span>
                      <div className="text-right">
                        <div>
                          {shipping === 0 ? "FREE" : formatPrice(shipping)}
                        </div>
                        {(selectedShippingRate ||
                          (checkoutSession?.shipping_carrier &&
                            checkoutSession?.shipping_service)) && (
                          <div className="text-xs text-gray-500">
                            {selectedShippingRate
                              ? `${selectedShippingRate.carrier} - ${selectedShippingRate.service}`
                              : `${checkoutSession.shipping_carrier} - ${checkoutSession.shipping_service}`}
                          </div>
                        )}
                      </div>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span>Tax:</span>
                      <span>{formatPrice(tax)}</span>
                    </div>
                  </>
                )}
                <div className="flex justify-between text-lg font-bold border-t pt-2">
                  <span>Total:</span>
                  <span>{formatPrice(total)}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
