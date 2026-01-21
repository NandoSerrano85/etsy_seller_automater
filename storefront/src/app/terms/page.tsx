export default function TermsPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">Terms of Service</h1>

      <div className="prose prose-lg">
        <p className="text-sm text-gray-600 mb-8">
          Last updated: {new Date().toLocaleDateString()}
        </p>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Agreement to Terms</h2>
          <p>
            By accessing and using CraftFlow Commerce, you agree to be bound by
            these Terms of Service and all applicable laws and regulations. If
            you do not agree with any of these terms, you are prohibited from
            using this site.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Use License</h2>
          <p>
            Permission is granted to temporarily download one copy of the
            materials on CraftFlow Commerce's website for personal,
            non-commercial transitory viewing only. This is the grant of a
            license, not a transfer of title.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Product Descriptions</h2>
          <p>
            We strive to provide accurate product descriptions and images.
            However, we do not warrant that product descriptions, images, or
            other content is accurate, complete, reliable, current, or
            error-free.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Pricing</h2>
          <p>
            All prices are subject to change without notice. We reserve the
            right to modify or discontinue products at any time. We are not
            liable for any price changes or discontinuation of products.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Account Terms</h2>
          <ul>
            <li>You must be 18 years or older to use this service</li>
            <li>
              You are responsible for maintaining the security of your account
            </li>
            <li>
              You are responsible for all activities that occur under your
              account
            </li>
            <li>You must not use the service for any illegal purpose</li>
          </ul>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Order Cancellation</h2>
          <p>
            We reserve the right to refuse or cancel any order for any reason,
            including but not limited to product availability, errors in pricing
            or product information, or suspected fraudulent activity.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            Limitation of Liability
          </h2>
          <p>
            CraftFlow Commerce shall not be liable for any damages arising out
            of or related to your use of or inability to use the service, even
            if we have been advised of the possibility of such damages.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">
            Modifications to Terms
          </h2>
          <p>
            We reserve the right to modify these terms at any time. Changes will
            be effective immediately upon posting. Your continued use of the
            service after changes constitutes acceptance of the modified terms.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Contact</h2>
          <p>
            Questions about the Terms of Service should be sent to us at{" "}
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
