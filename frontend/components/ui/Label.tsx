  // components/ui/Label.tsx
  import React from 'react';

  interface LabelProps extends React.LabelHTMLAttributes<HTMLLabelElement> {}

  const Label: React.FC<LabelProps> = ({ children, ...props }) => {
    return (
      <label {...props} className="block text-xs mb-2">
        {children}
      </label>
    );
  };

  export default Label;