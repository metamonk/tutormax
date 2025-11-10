'use client';

import { usePathname, useRouter } from 'next/navigation';
import { useAuth } from '@/contexts';
import { cn } from '@/lib/utils';
import {
  LayoutDashboard,
  Users,
  UserCircle,
  AlertCircle,
  Home,
  Menu
} from 'lucide-react';
import { useState } from 'react';

interface NavItem {
  icon: any;
  label: string;
  href: string;
  requiresRole?: string[];
}

const NAV_ITEMS: NavItem[] = [
  {
    icon: Home,
    label: 'Home',
    href: '/',
  },
  {
    icon: LayoutDashboard,
    label: 'Dashboard',
    href: '/dashboard',
  },
  {
    icon: UserCircle,
    label: 'Portal',
    href: '/tutor-portal',
    requiresRole: ['tutor', 'admin'],
  },
  {
    icon: AlertCircle,
    label: 'Interventions',
    href: '/interventions',
    requiresRole: ['operations', 'admin'],
  },
  {
    icon: Users,
    label: 'Users',
    href: '/users',
    requiresRole: ['admin'],
  },
];

export function MobileNav() {
  const pathname = usePathname();
  const router = useRouter();
  const { hasRole, isAuthenticated } = useAuth();
  const [touchStart, setTouchStart] = useState<number | null>(null);
  const [touchEnd, setTouchEnd] = useState<number | null>(null);

  // Filter items based on user roles
  const visibleItems = NAV_ITEMS.filter(item => {
    if (!item.requiresRole) return true;
    if (!isAuthenticated) return false;
    return item.requiresRole.some(role => hasRole(role as any));
  });

  // Handle swipe gestures
  const minSwipeDistance = 50;

  const onTouchStart = (e: React.TouchEvent) => {
    setTouchEnd(null);
    setTouchStart(e.targetTouches[0].clientX);
  };

  const onTouchMove = (e: React.TouchEvent) => {
    setTouchEnd(e.targetTouches[0].clientX);
  };

  const onTouchEnd = () => {
    if (!touchStart || !touchEnd) return;

    const distance = touchStart - touchEnd;
    const isLeftSwipe = distance > minSwipeDistance;
    const isRightSwipe = distance < -minSwipeDistance;

    const currentIndex = visibleItems.findIndex(item => item.href === pathname);

    if (isLeftSwipe && currentIndex < visibleItems.length - 1) {
      router.push(visibleItems[currentIndex + 1].href);
    }

    if (isRightSwipe && currentIndex > 0) {
      router.push(visibleItems[currentIndex - 1].href);
    }
  };

  return (
    <nav
      className="fixed bottom-0 left-0 right-0 bg-white dark:bg-gray-900 border-t border-gray-200 dark:border-gray-800 z-40 md:hidden safe-area-inset-bottom"
      onTouchStart={onTouchStart}
      onTouchMove={onTouchMove}
      onTouchEnd={onTouchEnd}
    >
      <div className="flex items-center justify-around h-16 px-2">
        {visibleItems.map((item) => {
          const Icon = item.icon;
          const isActive = pathname === item.href ||
            (item.href !== '/' && pathname.startsWith(item.href));

          return (
            <button
              key={item.href}
              onClick={() => router.push(item.href)}
              className={cn(
                'flex flex-col items-center justify-center gap-1 px-3 py-2 rounded-lg transition-all min-w-[64px] min-h-[48px]',
                'active:scale-95',
                isActive
                  ? 'text-blue-600 dark:text-blue-400 bg-blue-50 dark:bg-blue-950'
                  : 'text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800'
              )}
              aria-label={item.label}
            >
              <Icon className={cn(
                'h-5 w-5',
                isActive && 'animate-pulse'
              )} />
              <span className="text-[10px] font-medium">{item.label}</span>
            </button>
          );
        })}
      </div>
    </nav>
  );
}
