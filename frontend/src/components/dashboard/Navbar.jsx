import React from "react";
import { TbBell, TbMenu } from "react-icons/tb";
import styles from "./Navbar.module.css";

const Navbar = ({ user, onMenuClick }) => {
  // Fallback if user is loading or null
  const currentUser = user || { full_name: "Health User", role: "Patient" };

  // Generate initials for avatar
  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  // Capitalize role name
  const formatRole = (role) => {
    if (!role) return "";
    return role.charAt(0).toUpperCase() + role.slice(1).toLowerCase();
  };

  return (
    <header className={styles.navbar}>
      <div className={styles.left}>
        <button
          className={styles.menuBtn}
          onClick={onMenuClick}
          aria-label="Open navigation menu"
        >
          <TbMenu size={24} />
        </button>

        <div className={styles.welcomeText}>
          <span className={styles.greeting}>Hello,</span>
          <h1 className={styles.userName}>{currentUser.full_name || "User"}</h1>
        </div>
      </div>

      <div className={styles.right}>
        {/* User Role Badge */}
        <span className={`${styles.roleBadge} ${styles[currentUser.role?.toLowerCase() || "patient"]}`}>
          {formatRole(currentUser.role)}
        </span>

        {/* Notification Bell */}
        <button className={styles.bellBtn} aria-label="Notifications">
          <TbBell size={22} />
          <span className={styles.bellDot} />
        </button>

        {/* User Initials Avatar */}
        <div className={styles.avatar}>
          <span>{getInitials(currentUser.full_name)}</span>
        </div>
      </div>
    </header>
  );
};

export default Navbar;
