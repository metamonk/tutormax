import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/contexts";
import { ThemeProvider } from "@/components/theme-provider";
import { Toaster } from "@/components/ui/sonner";
import { InstallPrompt, UpdateNotification, OfflineIndicator, MobileNav, ServiceWorkerRegistration } from "@/components/pwa";
import { Sidebar, SidebarProvider } from "@/components/sidebar";
import { AnimatedLayout } from "@/components/animated-layout";
import { MainContent } from "@/components/layout/MainContent";
import "./globals.css";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "TutorMax - Tutor Performance Evaluation",
  description: "Real-time tutor performance tracking and analytics platform",
  applicationName: "TutorMax",
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "TutorMax",
  },
  formatDetection: {
    telephone: false,
  },
  openGraph: {
    type: "website",
    siteName: "TutorMax",
    title: "TutorMax - Tutor Performance Evaluation",
    description: "Real-time tutor performance tracking and analytics",
  },
  twitter: {
    card: "summary",
    title: "TutorMax - Tutor Performance Evaluation",
    description: "Real-time tutor performance tracking and analytics",
  },
  manifest: "/manifest.json",
};

export const viewport: Viewport = {
  themeColor: "#3b82f6",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <link rel="icon" href="/icon-192x192.png" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased pb-safe`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange={false}
        >
          <AuthProvider>
            <SidebarProvider>
              <ServiceWorkerRegistration />
              <OfflineIndicator />
              <UpdateNotification />
              <div className="flex min-h-screen">
                <Sidebar />
                <MainContent>
                  <AnimatedLayout>
                    {children}
                  </AnimatedLayout>
                </MainContent>
              </div>
              <MobileNav />
              <InstallPrompt />
              <Toaster />
            </SidebarProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
