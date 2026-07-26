import React from 'react';

const CardContainer = ({ children, cols = 3, gap = 6 }) => {
  const gridCols = `grid-cols-1 md:grid-cols-${cols}`;
  return (
    <div className={`grid ${gridCols} gap-${gap}`}>
      {children}
    </div>
  );
};

export default CardContainer;
