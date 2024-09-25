/** @type {import('next').NextConfig} */
const nextConfig = {
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 
          process.env.NODE_ENV === 'development'
            ? 'http://localhost:5000/api/:path*'
            : '/api/:path*',
      },
    ]
  },
};

export default nextConfig;