"use client";

import { useEffect } from "react";
import { useRouter, usePathname } from "next/navigation";
import Link from "next/link";
import { useStore } from "@/store/useStore";
import { User, Package, MapPin, Settings, LogOut } from "lucide-react";

export default function AccountLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const { customer, isAuthenticated, logout } = useStore();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push(`/login?returnUrl=${encodeURIComponent(pathname)}`);
    }
  }, [isAuthenticated, router, pathname]);

  if (!isAuthenticated) {
    return null;
  }

  const navigation = [
    {
      name: "Account Overview",
      href: "/account",
      icon: User,
      current: pathname === "/account",
    },
    {
      name: "Orders",
      href: "/account/orders",
      icon: Package,
      current: pathname.startsWith("/account/orders"),
    },
    {
      name: "Addresses",
      href: "/account/addresses",
      icon: MapPin,
      current: pathname === "/account/addresses",
    },
    {
      name: "Profile",
      href: "/account/profile",
      icon: Settings,
      current: pathname === "/account/profile",
    },
  ];

  const handleLogout = () => {
    logout();
    router.push("/");
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container py-8">
        {/* Page Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900">My Account</h1>
          <p className="text-gray-600 mt-1">
            Welcome back, {customer?.first_name} {customer?.last_name}
          </p>
        </div>

        <div className="grid lg:grid-cols-4 gap-8">
          {/* Sidebar Navigation */}
          <div className="lg:col-span-1">
            <nav className="bg-white rounded-lg shadow-sm p-4 space-y-1">
              {navigation.map((item) => {
                const Icon = item.icon;
                return (
                  <Link
                    key={item.name}
                    href={item.href}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                      item.current
                        ? "bg-primary-50 text-primary-700"
                        : "text-gray-700 hover:bg-gray-50"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    {item.name}
                  </Link>
                );
              })}

              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-5 h-5" />
                Logout
              </button>
            </nav>
          </div>

          {/* Main Content */}
          <div className="lg:col-span-3">{children}</div>
        </div>
      </div>
    </div>
  );
}
