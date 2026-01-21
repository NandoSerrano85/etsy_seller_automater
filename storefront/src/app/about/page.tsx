export default function AboutPage() {
  return (
    <div className="container mx-auto px-4 py-12 max-w-4xl">
      <h1 className="text-4xl font-bold mb-8">About Us</h1>

      <div className="prose prose-lg">
        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Our Story</h2>
          <p>
            Welcome to CraftFlow Commerce! We are passionate about bringing
            high-quality, custom-designed products to our customers. Our journey
            started with a simple idea: to make beautiful, personalized items
            accessible to everyone.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Our Mission</h2>
          <p>
            Our mission is to provide exceptional products with outstanding
            customer service. We believe in the power of customization and the
            joy it brings to our customers when they receive something truly
            unique.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Quality Commitment</h2>
          <p>
            Every product we create is made with care and attention to detail.
            We use only the finest materials and the latest printing
            technologies to ensure your items look amazing and last for years to
            come.
          </p>
        </section>

        <section className="mb-8">
          <h2 className="text-2xl font-semibold mb-4">Contact Us</h2>
          <p>
            Have questions or feedback? We'd love to hear from you! Visit our{" "}
            <a href="/contact" className="text-blue-600 hover:underline">
              contact page
            </a>{" "}
            to get in touch.
          </p>
        </section>
      </div>
    </div>
  );
}
