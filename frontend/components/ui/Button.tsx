import React from "react";
import clsx from "clsx";
import { classes } from "@/styles/classes";

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
	variant?: "primary" | "secondary";
}

const Button: React.FC<ButtonProps> = ({
	children,
	variant = "primary",
	className,
	...props
}) => {
	const baseClasses = classes.button.container;
	const variantClasses =
		variant === "primary" ? classes.button.primary : classes.button.secondary;

	return (
		<button
			{...props}
			className={clsx(
				baseClasses,
				variantClasses,
				className,
				props.disabled && "opacity-50 cursor-not-allowed"
			)}
		>
			{children}
		</button>
	);
};

export default Button;
