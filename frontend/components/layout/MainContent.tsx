'use client';

import { useAuth } from '@/contexts';
import { cn } from '@/lib/utils';

export function MainContent({ children }: { children: React.ReactNode }) {
  const { isAuthenticated } = useAuth();

  return (
    <main
      className={cn(
        'flex-1 transition-all duration-200',
        isAuthenticated && 'md:ml-60'
      )}
    >
      {children}
    </main>
  );
}
