import React from 'react';
import { Link } from 'react-router-dom';
import styles from './Navbar.module.css';
import Logo from '../common/Logo';
import Button from '../common/Button';

const Navbar = () => {
  return (
    <nav className={styles.navbar}>
      <div className={styles.container}>
        <Logo subtitle />
        
        <div className={styles.actions}>
          <span className={styles.loginText}>Already have an account?</span>
          <Link to="/login">
            <Button variant="outline" className={styles.loginBtn}>Log in</Button>
          </Link>
        </div>
      </div>
    </nav>
  );
};

export default Navbar;
