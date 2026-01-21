"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import {
  PaymentElement,
  useStripe,
  useElements,
} from "@stripe/react-stripe-js";
import { useStore } from "@/store/useStore";
import { checkoutApi, customerApi } from "@/lib/api";
import { formatPrice } from "@/lib/utils";
import toast from "react-hot-toast";
import { Loader2, CreditCard } from "lucide-react";

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

interface PaymentFormProps {
  checkoutSession: any;
  shippingForm: ShippingFormData;
  total: number;
  onBack: () => void;
}

export default function PaymentForm({
  checkoutSession,
  shippingForm,
  total,
  onBack,
}: PaymentFormProps) {
  const router = useRouter();
  const { isAuthenticated, clearCart } = useStore();
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);

  const handlePaymentSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!stripe || !elements) {
      return;
    }

    setIsProcessing(true);

    try {
      // Confirm payment with Stripe
      const { error, paymentIntent } = await stripe.confirmPayment({
        elements,
        confirmParams: {
          return_url: `${window.location.origin}/checkout/success`,
        },
        redirect: "if_required",
      });

      if (error) {
        toast.error(error.message || "Payment failed");
        setIsProcessing(false);
        return;
      }

      if (paymentIntent && paymentIntent.status === "succeeded") {
        // Complete checkout with backend
        const order = await checkoutApi.complete({
          session_id: checkoutSession.session_id,
          payment_intent_id: paymentIntent.id,
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
        });

        // Auto-save address for authenticated customers (no checkbox needed)
        if (isAuthenticated) {
          try {
            // Check if this address already exists
            const existingAddresses = await customerApi.getAddresses();
            const addressExists = existingAddresses.some(
              (addr: any) =>
                addr.address1 === shippingForm.address1 &&
                addr.city === shippingForm.city &&
                addr.zip_code === shippingForm.zip_code,
            );

            // Only save if it's a new address
            if (!addressExists) {
              await customerApi.addAddress({
                first_name: shippingForm.first_name,
                last_name: shippingForm.last_name,
                address1: shippingForm.address1,
                address2: shippingForm.address2 || undefined,
                city: shippingForm.city,
                state: shippingForm.state,
                zip_code: shippingForm.zip_code,
                country: shippingForm.country,
                phone: shippingForm.phone || undefined,
                is_default_shipping: existingAddresses.length === 0, // Set as default if first address
                is_default_billing: existingAddresses.length === 0,
              });
            }
          } catch (error) {
            // Don't fail the checkout if address save fails
            console.error("Failed to save address:", error);
          }
        }

        // Clear cart
        await clearCart();

        // Redirect to success page
        router.push(`/checkout/success?order_number=${order.order_number}`);
      }
    } catch (error: any) {
      console.error("Payment error:", error);
      toast.error(error.response?.data?.detail || "Payment processing failed");
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <form onSubmit={handlePaymentSubmit}>
      <h2 className="text-2xl font-bold mb-6">Payment Information</h2>

      <div className="mb-6">
        <PaymentElement />
      </div>

      <div className="flex gap-4">
        <button
          type="button"
          onClick={onBack}
          className="flex-1 bg-gray-200 text-gray-700 py-3 px-6 rounded-lg font-semibold hover:bg-gray-300"
        >
          Back
        </button>
        <button
          type="submit"
          disabled={isProcessing || !stripe}
          className="flex-1 bg-primary-600 text-white py-3 px-6 rounded-lg font-semibold hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {isProcessing ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Processing...
            </>
          ) : (
            <>
              <CreditCard className="w-5 h-5" />
              Pay {formatPrice(total)}
            </>
          )}
        </button>
      </div>
    </form>
  );
}
