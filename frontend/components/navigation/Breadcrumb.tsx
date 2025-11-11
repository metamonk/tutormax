'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ChevronRight, Home } from 'lucide-react';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  href: string;
}

// Map paths to readable labels
const pathLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  'tutor-portal': 'Tutor Portal',
  interventions: 'Interventions',
  users: 'Users',
  admin: 'Admin',
  'audit-logs': 'Audit Logs',
  compliance: 'Compliance',
  training: 'Training',
  feedback: 'Feedback',
  monitoring: 'Monitoring',
  offline: 'Offline',
  tutor: 'Tutor',
};

export function Breadcrumb() {
  const pathname = usePathname();

  // Don't show breadcrumbs on home page or login
  if (pathname === '/' || pathname === '/login') {
    return null;
  }

  // Parse pathname into breadcrumb items
  const paths = pathname.split('/').filter(Boolean);
  const breadcrumbs: BreadcrumbItem[] = [
    { label: 'Home', href: '/' },
  ];

  let currentPath = '';
  paths.forEach((path) => {
    currentPath += `/${path}`;
    const label = pathLabels[path] || path.charAt(0).toUpperCase() + path.slice(1);
    breadcrumbs.push({
      label,
      href: currentPath,
    });
  });

  return (
    <nav
      aria-label="Breadcrumb"
      className="flex items-center space-x-2 text-sm text-muted-foreground mb-6"
    >
      <ol className="flex items-center space-x-2">
        {breadcrumbs.map((crumb, index) => {
          const isLast = index === breadcrumbs.length - 1;
          const isFirst = index === 0;

          return (
            <li key={crumb.href} className="flex items-center space-x-2">
              {index > 0 && (
                <ChevronRight className="h-4 w-4 shrink-0 text-muted-foreground/50" />
              )}
              {isLast ? (
                <span
                  className="font-medium text-foreground"
                  aria-current="page"
                >
                  {isFirst ? (
                    <Home className="h-4 w-4" />
                  ) : (
                    crumb.label
                  )}
                </span>
              ) : (
                <Link
                  href={crumb.href}
                  className={cn(
                    'transition-colors hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring rounded-sm px-1 py-0.5',
                    'flex items-center'
                  )}
                >
                  {isFirst ? (
                    <Home className="h-4 w-4" />
                  ) : (
                    crumb.label
                  )}
                </Link>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
