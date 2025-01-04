import React from "react";
import { cn } from "@/utils/cn";

interface BadgeProps {
	variant?: "success" | "info" | "warning" | "default";
	size?: "sm" | "md";
	children: React.ReactNode;
	className?: string;
}

export const Badge: React.FC<BadgeProps> = ({
	variant = "default",
	size = "md",
	children,
	className,
}) => {
	const variantStyles = {
		success: "bg-green-100 text-green-800",
		info: "bg-blue-100 text-blue-800",
		warning: "bg-yellow-100 text-yellow-800",
		default: "bg-gray-100 text-gray-800",
	};

	const sizeStyles = {
		sm: "text-xs px-2 py-1",
		md: "text-sm px-2 py-1",
	};

	return (
		<span
			className={cn(
				"font-medium rounded",
				variantStyles[variant],
				sizeStyles[size],
				className
			)}
		>
			{children}
		</span>
	);
};
