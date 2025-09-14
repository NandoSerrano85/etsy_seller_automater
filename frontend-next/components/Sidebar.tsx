'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';

export default function Sidebar() {
  const pathname = usePathname();

  const navItems = [
    { href: '/dashboard', label: 'Dashboard', icon: '📊' },
    { href: '/designs', label: 'Designs', icon: '🎨' },
    { href: '/mockup-creator', label: 'Mockup Creator', icon: '🖼️' },
    { href: '/shop', label: 'Shop', icon: '🏪' },
    { href: '/subscription', label: 'Subscription', icon: '💳' },
    { href: '/account', label: 'Account', icon: '⚙️' },
  ];

  const isActive = (href: string) => {
    return pathname === href;
  };

  return (
    <div className="w-64 bg-gray-900 text-white h-full">
      <div className="p-6">
        <div className="flex items-center space-x-3">
          <div className="w-8 h-8 bg-primary rounded-md flex items-center justify-center">
            <span className="text-sm font-bold text-white">CF</span>
          </div>
          <h2 className="text-lg font-semibold">Craft Flow</h2>
        </div>
      </div>

      <nav className="mt-6">
        <ul className="space-y-1">
          {navItems.map((item) => (
            <li key={item.href}>
              <Link
                href={item.href}
                className={`flex items-center px-6 py-3 text-sm font-medium transition-colors ${
                  isActive(item.href)
                    ? 'bg-primary text-white border-r-2 border-white'
                    : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                }`}
              >
                <span className="mr-3 text-base">{item.icon}</span>
                {item.label}
              </Link>
            </li>
          ))}
        </ul>
      </nav>
    </div>
  );
}