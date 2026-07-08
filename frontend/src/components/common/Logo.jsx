import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Logo.module.css';
import { TbPill } from 'react-icons/tb';

const Logo = ({ className = '', subtitle = false }) => {
  return (
    <Link to="/" className={`${styles.logoContainer} ${className}`}>
      <div className={styles.logoMain}>
        <TbPill className={styles.icon} />
        <span className={styles.text}>PillSync</span>
      </div>
      {subtitle && (
        <span className={styles.subtitle}>
          Intelligent Medicine Reminder Platform
        </span>
      )}
    </Link>
  );
};

export default Logo;
