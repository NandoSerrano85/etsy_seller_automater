'use client';

import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TenantProvider } from '@/context/TenantProvider';
import { useState } from 'react';

interface QueryClientWrapperProps {
  children: React.ReactNode;
}

export function QueryClientWrapper({ children }: QueryClientWrapperProps) {
  const [queryClient] = useState(() => new QueryClient());

  return (
    <QueryClientProvider client={queryClient}>
      <TenantProvider>
        {children}
      </TenantProvider>
    </QueryClientProvider>
  );
}