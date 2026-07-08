import React from 'react';
import styles from './AuthLayout.module.css';
import Logo from '../common/Logo';

const AuthLayout = ({ children, leftContent }) => {
  return (
    <div className={styles.layout}>
      <div className={styles.leftPane}>
        <div className={styles.logoWrapper}>
          <Logo subtitle />
        </div>
        <div className={styles.illustrationContent}>
          {leftContent}
        </div>
      </div>
      <div className={styles.rightPane}>
        <div className={styles.formContainer}>
          {children}
        </div>
      </div>
    </div>
  );
};

export default AuthLayout;
