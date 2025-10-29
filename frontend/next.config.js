/** @type {import('next').NextConfig} */
const nextConfig = {
  /* config options here */
  output: 'standalone',
  poweredByHeader: false,
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    typedRoutes: true,
  },
  async rewrites() {
    // Proxy backend auth endpoints during development so relative fetch('/auth/...') works.
    // Use localhost (not 127.0.0.1) to ensure cookie domain matches frontend origin so httpOnly session cookie is stored.
    return [
      {
        source: '/auth/:path*',
        // Use localhost to align cookie host with frontend dev server (localhost:3000)
        destination: 'http://localhost:8000/auth/:path*',
      },
    ];
  },
  // Performance budgets and monitoring
  webpack: (config, { dev, isServer }) => {
    // Bundle analyzer disabled for now to avoid ES module issues
    return config
  },
}

export default nextConfig