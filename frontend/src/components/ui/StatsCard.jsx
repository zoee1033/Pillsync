import React from 'react';
import PropTypes from 'prop-types';

const StatsCard = ({ title, series, footer }) => {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm w-full">
      <div className="flex items-center justify-between">
        <h4 className="text-sm text-text-secondary">{title}</h4>
        {footer}
      </div>

      <div className="mt-3">
        {/* Placeholder for chart - consumers can pass in a chart component */}
        {series || <div className="h-24 bg-gray-50 rounded" />}
      </div>
    </div>
  );
};

StatsCard.propTypes = {
  title: PropTypes.string,
  series: PropTypes.node,
  footer: PropTypes.node,
};

export default StatsCard;
