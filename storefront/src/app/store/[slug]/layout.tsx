import { Header } from "@/components/layout/Header";
import { Footer } from "@/components/layout/Footer";
import { CartSidebar } from "@/components/cart/CartSidebar";
import { StoreWrapper } from "@/components/StoreWrapper";

export default function StoreLayout({
  children,
  params,
}: {
  children: React.ReactNode;
  params: { slug: string };
}) {
  return (
    <StoreWrapper>
      <Header />
      <main className="flex-1">{children}</main>
      <Footer />
      <CartSidebar />
    </StoreWrapper>
  );
}
