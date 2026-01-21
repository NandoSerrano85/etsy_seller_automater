import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "CraftFlow Storefront - Multi-Tenant Ecommerce",
  description: "Create and host your own ecommerce store with CraftFlow.",
  keywords: ["ecommerce", "storefront", "multi-tenant", "online store"],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className={inter.variable}>
      <body className="min-h-screen flex flex-col">
        <Providers>
          <main className="flex-1">{children}</main>
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
