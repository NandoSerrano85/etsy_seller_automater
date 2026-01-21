export default function PrivacyPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Privacy Policy</h1>

      <div className="prose prose-lg">
        <p className="text-sm text-gray-600 mb-8">
          Last updated: {new Date().toLocaleDateString()}
        </p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Introduction</h2>
          <p>
            At CraftFlow Commerce, we respect your privacy and are committed to
            protecting your personal information. This Privacy Policy explains
            how we collect, use, and safeguard your data when you use our
            services.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            Information We Collect
          </h2>
          <ul>
            <li>
              <strong>Personal Information:</strong> Name, email address,
              shipping address, phone number
            </li>
            <li>
              <strong>Payment Information:</strong> Credit card details
              (processed securely through our payment processor)
            </li>
            <li>
              <strong>Order Information:</strong> Products purchased, order
              history
            </li>
            <li>
              <strong>Technical Data:</strong> IP address, browser type, device
              information
            </li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            How We Use Your Information
          </h2>
          <ul>
            <li>Process and fulfill your orders</li>
            <li>Communicate with you about your orders</li>
            <li>Send marketing communications (with your consent)</li>
            <li>Improve our products and services</li>
            <li>Prevent fraud and maintain security</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Data Security</h2>
          <p>
            We implement industry-standard security measures to protect your
            personal information. All payment information is encrypted and
            processed through secure payment gateways.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Your Rights</h2>
          <p>You have the right to:</p>
          <ul>
            <li>Access your personal data</li>
            <li>Request correction of inaccurate data</li>
            <li>Request deletion of your data</li>
            <li>Opt-out of marketing communications</li>
            <li>Request a copy of your data</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Cookies</h2>
          <p>
            We use cookies to enhance your browsing experience and analyze site
            traffic. You can control cookie settings through your browser
            preferences.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
          <p>
            If you have questions about this Privacy Policy, please contact us
            at{" "}
            <a href="/contact" className="text-blue-600 hover:underline">
              our contact page
            </a>
            .
          </p>
        </section>
      </div>
    </div>
  );
}
