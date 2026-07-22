import React from 'react';
import PropTypes from 'prop-types';

const StatusBadge = ({ status }) => {
  const map = {
    active: 'bg-primary-green/20 text-primary-green',
    completed: 'bg-green-100 text-green-700',
    pending: 'bg-orange-100 text-orange-700',
    missed: 'bg-red-100 text-red-700',
  };

  const cls = map[status?.toLowerCase()] || 'bg-gray-100 text-text-secondary';

  return (
    <span className={`px-3 py-1 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  );
};

StatusBadge.propTypes = {
  status: PropTypes.string,
};

export default StatusBadge;
