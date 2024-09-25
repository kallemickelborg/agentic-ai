  // components/ui/Input.tsx
  import React from 'react';

  interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

  const Input: React.FC<InputProps> = (props) => {
    return (
      <input
        {...props}
        className="mt-1 w-full border-2 border-gray-300 rounded-md p-2 rounded-lg shadow-lg"
      />
    );
  };

  export default Input;