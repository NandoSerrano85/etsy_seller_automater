"use client";

import { useBranding } from "@/contexts/BrandingContext";

export function BenefitsSection() {
  const { settings } = useBranding();

  const benefits = [
    {
      icon: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M5 13l4 4L19 7"
        />
      ),
      title: "Premium Quality",
      description: "High-quality materials and printing",
    },
    {
      icon: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      ),
      title: "Fast Shipping",
      description: "Quick processing and delivery",
    },
    {
      icon: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      ),
      title: "Easy to Apply",
      description: "Simple application instructions included",
    },
    {
      icon: (
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M14 10h4.764a2 2 0 011.789 2.894l-3.5 7A2 2 0 0115.263 21h-4.017c-.163 0-.326-.02-.485-.06L7 20m7-10V5a2 2 0 00-2-2h-.095c-.5 0-.905.405-.905.905 0 .714-.211 1.412-.608 2.006L7 11v9m7-10h-2M7 20H5a2 2 0 01-2-2v-6a2 2 0 012-2h2.5"
        />
      ),
      title: "Satisfaction Guaranteed",
      description: "100% satisfaction or your money back",
    },
  ];

  // Helper to lighten color for background
  const lightenColor = (color: string, percent: number = 90) => {
    const num = parseInt(color.replace("#", ""), 16);
    const r = (num >> 16) + Math.round((255 - (num >> 16)) * (percent / 100));
    const g =
      ((num >> 8) & 0x00ff) +
      Math.round((255 - ((num >> 8) & 0x00ff)) * (percent / 100));
    const b =
      (num & 0x0000ff) + Math.round((255 - (num & 0x0000ff)) * (percent / 100));
    return `rgb(${Math.min(r, 255)}, ${Math.min(g, 255)}, ${Math.min(b, 255)})`;
  };

  return (
    <section className="py-16">
      <div className="container">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
          {benefits.map((benefit, index) => (
            <div key={index}>
              <div
                className="w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4"
                style={{
                  backgroundColor: lightenColor(settings.primary_color, 90),
                }}
              >
                <svg
                  className="w-8 h-8"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                  style={{ color: settings.primary_color }}
                >
                  {benefit.icon}
                </svg>
              </div>
              <h3 className="font-bold mb-2">{benefit.title}</h3>
              <p className="text-gray-600 text-sm">{benefit.description}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
