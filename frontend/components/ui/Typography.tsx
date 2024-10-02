  // components/ui/Typography.tsx
  import React from 'react';

  interface TypographyProps extends React.HTMLAttributes<HTMLHeadingElement | HTMLParagraphElement> {
    variant: 'h1' | 'h2' | 'h3' | 'p';
  }

  const Typography: React.FC<TypographyProps> = ({ variant, children, ...props }) => {
    const baseClasses = 'font-semibold';
    const variantClasses = variant === 'h1'
      ? 'text-lg'
      : variant === 'h2'
        ? 'text-md'
        : variant === 'h3'
          ? 'text-sm'
          : variant === 'p'
            ? 'text-xs'
            : 'text-base';

    const Component = variant.startsWith('h') ? variant : 'p';

    return (
      <Component {...props} className={`${baseClasses} ${variantClasses} ${props.className}`}>
        {children}
      </Component>
    );
  };

  export default Typography;