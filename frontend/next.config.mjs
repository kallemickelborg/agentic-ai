/** @type {import('next').NextConfig} */
const nextConfig = {
  images: {
    unoptimized: true,
  },
  env: {
    NEXT_PUBLIC_API_BASE_URL: 'https://agentic-ai-backend.onrender.com', //CHANGE THIS TO LOCALHOST WHEN RUNNING LOCALLY (http://localhost:8000)
  },
//   assetPrefix: './',
};

export default nextConfig;