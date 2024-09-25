import React from 'react';

interface ListItemProps extends React.LiHTMLAttributes<HTMLLIElement> {}

const ListItem: React.FC<ListItemProps> = ({ children, ...props }) => {
  return (
    <li {...props} className={`mb-2 ${props.className}`}>
      {children}
    </li>
  );
};

export default ListItem;