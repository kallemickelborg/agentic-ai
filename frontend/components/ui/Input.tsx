// components/ui/Input.tsx
import React from "react";
import { classes } from "@/styles/classes";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input: React.FC<InputProps> = (props) => {
	return <input {...props} className={classes.item.input} />;
};

export default Input;
