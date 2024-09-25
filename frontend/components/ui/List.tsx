  // components/ui/List.tsx
  import React from 'react';

  interface ListProps extends React.HTMLAttributes<HTMLUListElement> {}

  const List: React.FC<ListProps> = ({ children, ...props }) => {
    return (
      <ul {...props} className={`list-disc list-inside ${props.className}`}>
        {children}
      </ul>
    );
  };

  export default List;