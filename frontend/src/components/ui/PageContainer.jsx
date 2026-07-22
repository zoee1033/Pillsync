import React from 'react';

const PageContainer = ({ children }) => {
  return (
    <div className="max-w-6xl mx-auto">
      {children}
    </div>
  );
};

export default PageContainer;
