'use client';

import { useState } from 'react';

export default function HomePage() {
  const [authUrl, setAuthUrl] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);

  const handleConnectEtsy = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.NEXT_PUBLIC_API_URL}/api/oauth-data`
      );
      const data = await response.json();
      setAuthUrl(data.authUrl);
    } catch (error) {
      console.error('Error fetching OAuth data:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-full flex flex-col items-center justify-center">
      <div className="text-center">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Welcome to Etsy Seller Automator
        </h1>
        <p className="text-lg text-gray-600 mb-8">
          Connect your Etsy store to automate your selling experience
        </p>

        <button
          onClick={handleConnectEtsy}
          disabled={loading}
          className="bg-primary text-white px-6 py-3 rounded-md font-medium hover:bg-opacity-90 disabled:opacity-50"
        >
          {loading ? 'Connecting...' : 'Connect Etsy'}
        </button>

        {authUrl && (
          <div className="mt-6">
            <p className="text-sm text-gray-600 mb-2">
              Click the link below to authorize:
            </p>
            <a
              href={authUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline hover:text-opacity-80"
            >
              {authUrl}
            </a>
          </div>
        )}
      </div>
    </div>
  );
}
