import React from 'react';
import PropTypes from 'prop-types';

const EmptyState = ({ title = 'Nothing here', message = 'No records found.', action }) => {
  return (
    <div className="bg-white border border-border rounded-xl p-8 text-center">
      <div className="text-3xl mb-3">📭</div>
      <h3 className="text-lg font-semibold text-text-primary">{title}</h3>
      <p className="text-sm text-text-secondary mt-2">{message}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
};

EmptyState.propTypes = {
  title: PropTypes.string,
  message: PropTypes.string,
  action: PropTypes.node,
};

export default EmptyState;
