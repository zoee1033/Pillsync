import React from 'react';

const LoadingSkeleton = ({ lines = 3 }) => {
  return (
    <div className="space-y-2">
      {Array.from({ length: lines }).map((_, i) => (
        <div key={i} className="h-3 bg-gray-200 rounded w-full animate-pulse" />
      ))}
    </div>
  );
};

export default LoadingSkeleton;
