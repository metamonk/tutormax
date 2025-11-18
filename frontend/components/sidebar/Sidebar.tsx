'use client';

import type React from 'react';
import { useState } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import {
  Home,
  LayoutDashboard,
  UserCircle,
  AlertCircle,
  Users,
  ChevronDown,
  ChevronRight,
  Menu,
  User,
  LogOut,
  Settings,
  FileText,
  Shield,
  GraduationCap,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSidebar } from './sidebar-context';
import { useAuth } from '@/contexts';
import { ThemeToggle } from '@/components/theme-toggle';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
  requiresRole?: string[];
  subItems?: NavItem[];
}

const navigationItems: NavItem[] = [
  {
    label: 'Home',
    href: '/',
    icon: Home,
  },
  {
    label: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
  },
  {
    label: 'Tutor Portal',
    href: '/tutor-portal',
    icon: UserCircle,
    requiresRole: ['tutor', 'admin'],
  },
  {
    label: 'Interventions',
    href: '/interventions',
    icon: AlertCircle,
    requiresRole: ['operations', 'admin'],
  },
  {
    label: 'Users',
    href: '/users',
    icon: Users,
    requiresRole: ['admin'],
  },
  {
    label: 'Admin',
    href: '/admin',
    icon: Shield,
    requiresRole: ['admin'],
    subItems: [
      {
        label: 'Audit Logs',
        href: '/admin/audit-logs',
        icon: FileText,
      },
      {
        label: 'Compliance',
        href: '/admin/compliance',
        icon: Shield,
      },
      {
        label: 'Training',
        href: '/admin/training',
        icon: GraduationCap,
      },
    ],
  },
];

export function Sidebar() {
  const { isOpen, toggle } = useSidebar();
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, hasRole, logout } = useAuth();
  const [expandedItems, setExpandedItems] = useState<string[]>([]);

  // Filter nav items based on user role
  const filteredNavItems = navigationItems.filter((item) => {
    if (!item.requiresRole) return true;
    if (!isAuthenticated) return false;
    return item.requiresRole.some((role) => hasRole(role as any));
  });

  const toggleExpanded = (label: string) => {
    setExpandedItems((prev) =>
      prev.includes(label) ? prev.filter((item) => item !== label) : [...prev, label]
    );
  };

  const isActive = (href: string) => {
    return pathname === href || (href !== '/' && pathname.startsWith(href));
  };

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  if (!isAuthenticated) {
    return null;
  }

  return (
    <aside
      className={cn(
        'fixed left-0 top-0 z-40 h-screen bg-sidebar border-r border-sidebar-border transition-all duration-200 ease-in-out hidden md:block',
        isOpen ? 'w-60' : 'w-16'
      )}
    >
      <div className="flex h-full flex-col">
        {/* Logo and Toggle */}
        <div className="flex h-16 items-center justify-between border-b border-sidebar-border px-4">
          <div
            className={cn(
              'flex items-center gap-3 transition-opacity duration-200',
              !isOpen && 'opacity-0'
            )}
          >
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sidebar-primary">
              <GraduationCap className="h-5 w-5 text-sidebar-primary-foreground" />
            </div>
            <span className="text-base font-semibold text-sidebar-foreground">TutorMax</span>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={toggle}
            className={cn(
              'h-9 w-9 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground',
              !isOpen && 'mx-auto'
            )}
            aria-label={isOpen ? 'Collapse sidebar' : 'Expand sidebar'}
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 space-y-1 overflow-y-auto p-3">
          {filteredNavItems.map((item) => {
            const Icon = item.icon;
            const hasSubItems = item.subItems && item.subItems.length > 0;
            const isExpanded = expandedItems.includes(item.label);
            const isItemActive = isActive(item.href);

            return (
              <div key={item.label}>
                <Link
                  href={item.href}
                  onClick={(e) => {
                    if (hasSubItems) {
                      e.preventDefault();
                      toggleExpanded(item.label);
                    }
                  }}
                  className={cn(
                    'group flex h-11 items-center gap-3 rounded-lg px-3 text-sm font-medium transition-all duration-200',
                    'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring',
                    isItemActive
                      ? 'bg-sidebar-primary text-sidebar-primary-foreground shadow-sm'
                      : 'text-sidebar-foreground',
                    !isOpen && 'justify-center'
                  )}
                  aria-label={!isOpen ? item.label : undefined}
                  title={!isOpen ? item.label : undefined}
                >
                  <Icon className="h-5 w-5 shrink-0" />
                  {isOpen && (
                    <>
                      <span className="flex-1">{item.label}</span>
                      {hasSubItems && (
                        <div className="transition-transform duration-200">
                          {isExpanded ? (
                            <ChevronDown className="h-4 w-4" />
                          ) : (
                            <ChevronRight className="h-4 w-4" />
                          )}
                        </div>
                      )}
                    </>
                  )}
                </Link>

                {/* Sub-items */}
                {hasSubItems && isOpen && isExpanded && (
                  <div className="mt-1 space-y-1 pl-11">
                    {item.subItems!.map((subItem) => (
                      <Link
                        key={subItem.href}
                        href={subItem.href}
                        className={cn(
                          'flex h-9 items-center rounded-lg px-3 text-sm transition-all duration-200',
                          'hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sidebar-ring',
                          isActive(subItem.href)
                            ? 'bg-sidebar-accent text-sidebar-accent-foreground font-medium'
                            : 'text-sidebar-foreground/80'
                        )}
                      >
                        {subItem.label}
                      </Link>
                    ))}
                  </div>
                )}
              </div>
            );
          })}
        </nav>

        {/* User Profile and Theme Toggle */}
        <div className="border-t border-sidebar-border p-3">
          {/* Theme Toggle */}
          <div
            className={cn(
              'mb-2 flex',
              isOpen ? 'justify-start' : 'justify-center'
            )}
          >
            <ThemeToggle />
          </div>

          {/* User Profile Dropdown */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className={cn(
                  'h-14 w-full justify-start gap-3 text-sidebar-foreground hover:bg-sidebar-accent hover:text-sidebar-accent-foreground focus-visible:ring-2 focus-visible:ring-sidebar-ring',
                  !isOpen && 'justify-center px-0'
                )}
                aria-label={!isOpen ? 'User menu' : undefined}
              >
                <Avatar className="h-8 w-8 shrink-0">
                  <AvatarFallback className="bg-sidebar-primary text-sidebar-primary-foreground text-sm">
                    {user?.full_name && typeof user.full_name === 'string'
                      ? user.full_name
                          .split(' ')
                          .filter((n) => n.length > 0)
                          .map((n) => n[0])
                          .join('')
                          .toUpperCase()
                          .slice(0, 2) || 'U'
                      : 'U'}
                  </AvatarFallback>
                </Avatar>
                {isOpen && (
                  <div className="flex flex-col items-start text-left">
                    <span className="text-sm font-medium leading-none">{user?.full_name}</span>
                    <span className="text-xs text-sidebar-foreground/60 mt-1">{user?.email}</span>
                  </div>
                )}
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
              align={isOpen ? 'end' : 'center'}
              side={isOpen ? 'top' : 'right'}
              className="w-56"
            >
              <DropdownMenuLabel>My Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => router.push('/')}>
                <User className="mr-2 h-4 w-4" />
                <span>Profile</span>
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="mr-2 h-4 w-4" />
                <span>Settings</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                className="text-destructive focus:text-destructive"
                onClick={handleLogout}
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Log out</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </aside>
  );
}
