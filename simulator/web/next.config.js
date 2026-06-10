/** @type {import('next').NextConfig} */
const BACKEND = process.env.NEXT_PUBLIC_API || "http://localhost:5000";

module.exports = {
  reactStrictMode: true,
  // Proxy API + portrait requests to the Flask backend so the whole app is
  // same-origin from the browser's point of view (no CORS, one URL to open).
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND}/api/:path*` },
      { source: "/portraits/:path*", destination: `${BACKEND}/portraits/:path*` },
    ];
  },
};
