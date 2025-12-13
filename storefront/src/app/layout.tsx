import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Providers } from "./providers";
import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { CartSidebar } from "@/components/cart/CartSidebar";
import { Toaster } from "react-hot-toast";

const inter = Inter({ subsets: ["latin"], variable: "--font-inter" });

export const metadata: Metadata = {
  title: "Ecommerce Storefront - Custom Transfers & Designs",
  description:
    "Shop high-quality UVDTF, DTF, and sublimation transfers for all your crafting needs.",
  keywords: ["UVDTF", "DTF", "Sublimation", "Transfers", "Cup Wraps", "Vinyl"],
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
          <Header />
          <main className="flex-1">{children}</main>
          <Footer />
          <CartSidebar />
          <Toaster position="top-right" />
        </Providers>
      </body>
    </html>
  );
}
