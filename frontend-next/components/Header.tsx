'use client';

export default function Header() {
  return (
    <header className="bg-white border-b border-gray-200">
      <div className="flex items-center justify-between px-6 py-4">
        <div className="flex items-center space-x-2">
          <div className="w-8 h-8 bg-gray-500 rounded-lg flex items-center justify-center">
            <span className="text-white font-bold text-sm">JD</span>
          </div>
          <span className="text-xl font-semibold text-gray-900 hidden sm:block">
            Your Organization - John Doe
          </span>
        </div>

        <div className="flex items-center space-x-4">
          {/* Future: notifications, user menu, etc. */}
        </div>
      </div>
    </header>
  );
}