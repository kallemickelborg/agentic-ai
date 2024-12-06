/** @type {import('next').NextConfig} */
const nextConfig = {
	images: {
		unoptimized: true,
	},
	env: {
		NEXT_PUBLIC_API_BASE_URL:
			process.env.NODE_ENV === "development"
				? "http://localhost:8000"
				: "https://agentic-ai-backend.onrender.com",
	},
};

export default nextConfig;
