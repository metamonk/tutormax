'use client';

import type React from 'react';
import { createContext, useContext, useState, useEffect } from 'react';

interface SidebarContextType {
  isOpen: boolean;
  toggle: () => void;
  setIsOpen: (open: boolean) => void;
}

const SidebarContext = createContext<SidebarContextType | undefined>(undefined);

export function SidebarProvider({ children }: { children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(true);

  // Persist sidebar state to localStorage
  useEffect(() => {
    const stored = localStorage.getItem('sidebar-open');
    if (stored !== null) {
      setIsOpen(stored === 'true');
    }
  }, []);

  const toggle = () => {
    setIsOpen((prev) => {
      const newValue = !prev;
      localStorage.setItem('sidebar-open', String(newValue));
      return newValue;
    });
  };

  const handleSetIsOpen = (open: boolean) => {
    setIsOpen(open);
    localStorage.setItem('sidebar-open', String(open));
  };

  return (
    <SidebarContext.Provider value={{ isOpen, toggle, setIsOpen: handleSetIsOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const context = useContext(SidebarContext);
  if (context === undefined) {
    throw new Error('useSidebar must be used within a SidebarProvider');
  }
  return context;
}
