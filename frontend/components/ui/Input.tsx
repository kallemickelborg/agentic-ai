// components/ui/Input.tsx
import React from "react";

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input: React.FC<InputProps> = (props) => {
	return <input {...props} className="border p-2 w-[90%] flex mx-auto" />;
};

export default Input;
