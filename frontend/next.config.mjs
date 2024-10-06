/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: 'http://localhost:8000', //CHANGE THIS TO LOCALHOST WHEN RUNNING LOCALLY (https://agentic-ai-backend.onrender.com)
  },
//   assetPrefix: './',
};

export default nextConfig;