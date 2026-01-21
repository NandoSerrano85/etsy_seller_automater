export default function ShippingPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Shipping Information</h1>

      <div className="prose prose-lg">
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Processing Time</h2>
          <p>Orders are typically processed within 1-3 business days.</p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Shipping Methods</h2>
          <ul>
            <li>
              <strong>Standard Shipping:</strong> 5-7 business days
            </li>
            <li>
              <strong>Express Shipping:</strong> 2-3 business days
            </li>
            <li>
              <strong>Overnight Shipping:</strong> 1 business day
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Shipping Costs</h2>
          <p>
            Shipping costs are calculated at checkout based on your location and
            selected shipping method.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            International Shipping
          </h2>
          <p>
            We currently ship within the United States. International shipping
            is not available at this time.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Tracking Your Order</h2>
          <p>
            Once your order ships, you will receive a tracking number via email.
            You can also track your order in your account dashboard.
          </p>
        </section>
      </div>
    </div>
  );
}
