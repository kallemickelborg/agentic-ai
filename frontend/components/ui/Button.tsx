import React from 'react';
import clsx from 'clsx';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary';
}

const Button: React.FC<ButtonProps> = ({ children, variant = 'primary', className, ...props }) => {
  const baseClasses = 'flex mx-auto items-center justify-center text-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none';
  const variantClasses = variant === 'primary'
    ? 'text-white bg-indigo-600 hover:bg-indigo-700'
    : 'text-gray-700 bg-gray-200 hover:bg-gray-300';

  return (
    <button
      {...props}
      className={clsx(baseClasses, variantClasses, className, props.disabled && 'opacity-50 cursor-not-allowed')}
    >
      {children}
    </button>
  );
};

export default Button;