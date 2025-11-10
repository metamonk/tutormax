import type { Metadata, Viewport } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import { AuthProvider } from "@/contexts";
import { Toaster } from "@/components/ui/sonner";
import { InstallPrompt, UpdateNotification, OfflineIndicator, MobileNav, ServiceWorkerRegistration } from "@/components/pwa";
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
    <html lang="en">
      <head>
        <link rel="icon" href="/icon-192x192.png" />
        <link rel="apple-touch-icon" href="/icon-192x192.png" />
        <meta name="mobile-web-app-capable" content="yes" />
      </head>
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased pb-safe`}
      >
        <AuthProvider>
          <ServiceWorkerRegistration />
          <OfflineIndicator />
          <UpdateNotification />
          {children}
          <MobileNav />
          <InstallPrompt />
          <Toaster />
        </AuthProvider>
      </body>
    </html>
  );
}
