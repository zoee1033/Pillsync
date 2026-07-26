import React from 'react';
import PropTypes from 'prop-types';

const SummaryCard = ({ title, value, hint, icon }) => {
  return (
    <div className="bg-card border border-border rounded-xl p-4 shadow-sm w-full">
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-text-secondary">{title}</p>
          <h3 className="text-xl font-semibold text-text-primary mt-1">{value}</h3>
        </div>
        {icon && <div className="ml-4">{icon}</div>}
      </div>
      {hint && <p className="text-xs text-text-secondary mt-3">{hint}</p>}
    </div>
  );
};

SummaryCard.propTypes = {
  title: PropTypes.string,
  value: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
  hint: PropTypes.string,
  icon: PropTypes.node,
};

export default SummaryCard;
