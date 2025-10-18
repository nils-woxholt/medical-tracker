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
  // Performance budgets and monitoring
  webpack: (config, { dev, isServer }) => {
    // Bundle analyzer disabled for now to avoid ES module issues
    return config
  },
}

export default nextConfig