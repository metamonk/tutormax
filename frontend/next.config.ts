import type { NextConfig } from "next";
// @ts-ignore - next-pwa types are for Next 13, but works with Next 16
import withPWA from "next-pwa";
// @ts-ignore - bundle analyzer types
import withBundleAnalyzer from "@next/bundle-analyzer";

const nextConfig: NextConfig = {
  reactStrictMode: true,

  // Image optimization
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'localhost',
      },
      {
        protocol: 'https',
        hostname: 'localhost',
      },
    ],
    formats: ['image/avif', 'image/webp'],
  },

  // Compiler optimizations
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },

  // Production optimizations
  productionBrowserSourceMaps: false, // Disable source maps in production for faster builds

  // Experimental features for performance
  experimental: {
    optimizeCss: true,
    optimizePackageImports: ['lucide-react', '@radix-ui/react-icons', 'recharts', 'date-fns'],
  },

  // Output optimization
  output: 'standalone', // Optimize for Docker deployment

  // Turbopack configuration (Next.js 16+ default)
  turbopack: {},

  // Webpack optimizations (fallback for --webpack flag)
  webpack: (config, { dev, isServer }) => {
    // Only enable in production
    if (!dev && !isServer) {
      // Split chunks more aggressively
      config.optimization = {
        ...config.optimization,
        splitChunks: {
          chunks: 'all',
          cacheGroups: {
            default: false,
            vendors: false,
            // Vendor chunk for node_modules
            vendor: {
              name: 'vendor',
              chunks: 'all',
              test: /node_modules/,
              priority: 20,
            },
            // Common components chunk
            common: {
              name: 'common',
              minChunks: 2,
              chunks: 'all',
              priority: 10,
              reuseExistingChunk: true,
              enforce: true,
            },
            // Chart.js and heavy libraries
            charts: {
              name: 'charts',
              test: /[\\/]node_modules[\\/](chart\.js|react-chartjs-2|recharts)[\\/]/,
              chunks: 'all',
              priority: 30,
            },
            // UI library chunk
            ui: {
              name: 'ui',
              test: /[\\/]node_modules[\\/](@radix-ui)[\\/]/,
              chunks: 'all',
              priority: 25,
            },
          },
        },
      };
    }
    return config;
  },
};

// Configure bundle analyzer (only when ANALYZE=true)
const withAnalyzer = withBundleAnalyzer({
  enabled: process.env.ANALYZE === 'true',
});

// Configure PWA
const pwaConfig = withPWA({
  dest: 'public',
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === 'development',
  // Workbox configuration
  runtimeCaching: [
    {
      urlPattern: /^https?:\/\/localhost/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'api-cache',
        expiration: {
          maxEntries: 100,
          maxAgeSeconds: 60 * 60, // 1 hour
        },
      },
    },
    {
      urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|avif)$/,
      handler: 'CacheFirst',
      options: {
        cacheName: 'images-cache',
        expiration: {
          maxEntries: 200,
          maxAgeSeconds: 60 * 60 * 24 * 30, // 30 days
        },
      },
    },
    {
      urlPattern: /^https?.*/,
      handler: 'NetworkFirst',
      options: {
        cacheName: 'offlineCache',
        expiration: {
          maxEntries: 200,
        },
      },
    },
  ],
});

// @ts-ignore - compose the plugins
export default withAnalyzer(pwaConfig(nextConfig));
