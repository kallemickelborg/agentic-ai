/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: 'https://agentic-ai-backend.onrender.com',
  },
//   assetPrefix: './',
};

export default nextConfig;