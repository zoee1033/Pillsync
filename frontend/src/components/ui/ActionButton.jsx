import React from 'react';
import PropTypes from 'prop-types';

const ActionButton = ({ children, variant = 'primary', as: Component = 'button', className = '', ...props }) => {
  const base = 'px-4 py-2 rounded-full text-sm font-medium shadow-sm inline-flex items-center justify-center';
  const styles = {
    primary: `${base} bg-primary text-white`,
    outline: `${base} border border-border text-text-primary bg-white`,
  };

  return (
    <Component className={`${styles[variant] || styles.primary} ${className}`} {...props}>
      {children}
    </Component>
  );
};

ActionButton.propTypes = {
  children: PropTypes.node,
  variant: PropTypes.oneOf(['primary', 'outline']),
};

export default ActionButton;
