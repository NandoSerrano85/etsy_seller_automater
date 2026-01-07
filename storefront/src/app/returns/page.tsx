export default function ReturnsPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Returns & Exchanges</h1>

      <div className="prose prose-lg">
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">30-Day Return Policy</h2>
          <p>
            We offer a 30-day return policy for most items. Items must be
            unused, in original condition, and in original packaging.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">How to Return an Item</h2>
          <ol>
            <li>Contact our customer service team to initiate a return</li>
            <li>Package the item securely in its original packaging</li>
            <li>Ship the item back to us using the provided return label</li>
            <li>
              Refund will be processed within 5-7 business days after we receive
              your return
            </li>
          </ol>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Exchanges</h2>
          <p>
            If you received a damaged or defective item, please contact us
            immediately for a replacement or refund.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Non-Returnable Items</h2>
          <ul>
            <li>Custom or personalized items</li>
            <li>Final sale items</li>
            <li>Opened consumable products</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Refunds</h2>
          <p>
            Refunds will be issued to the original payment method. Shipping
            costs are non-refundable unless the return is due to our error.
          </p>
        </section>
      </div>
    </div>
  );
}
