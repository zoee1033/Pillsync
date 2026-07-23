import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  TbLayoutDashboard,
  TbUser,
  TbSettings,
  TbLogout,
  TbChevronLeft,
  TbChevronRight,
  TbPill,
  TbCalendarTime,
  TbClock,
  TbBell,
} from "react-icons/tb";
import Logo from "../common/Logo";
import styles from "./Sidebar.module.css";
import { removeToken } from "../../utils/token";

const Sidebar = ({ user, isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }) => {
  const navigate = useNavigate();

  const menuItems = [
    { path: "/dashboard", label: "Dashboard", icon: <TbLayoutDashboard size={22} /> },
    { path: "/profile", label: "Profile", icon: <TbUser size={22} /> },
    { path: "/treatments", label: "Treatments", icon: <TbPill size={22} /> },
    { path: "/medicines", label: "Medicines", icon: <TbPill size={22} /> },
    { path: "/reminders", label: "Reminders", icon: <TbCalendarTime size={22} /> },
    { path: "/notifications", label: "Notifications", icon: <TbBell size={22} /> },
    { path: "/history", label: "History", icon: <TbClock size={22} /> },
    { path: "/settings", label: "Settings", icon: <TbSettings size={22} /> },
  ];

  const handleLogout = () => {
    removeToken();
    localStorage.removeItem("user");
    navigate("/login");
  };

  const closeMobileSidebar = () => {
    if (isMobileOpen) {
      setIsMobileOpen(false);
    }
  };

  return (
    <>
      {/* Mobile Overlay backdrop */}
      {isMobileOpen && (
        <div
          className={styles.overlay}
          onClick={() => setIsMobileOpen(false)}
        />
      )}

      <aside
        className={`${styles.sidebar} ${
          isCollapsed ? styles.collapsed : ""
        } ${isMobileOpen ? styles.mobileOpen : ""}`}
      >
        <div className={styles.sidebarHeader}>
          {!isCollapsed ? (
            <Logo className={styles.logo} />
          ) : (
            <NavLink to="/dashboard" className={styles.logoCompact}>
              <span className={styles.logoIcon}>💊</span>
            </NavLink>
          )}

          {/* Collapse toggle for Desktop */}
          <button
            className={styles.toggleBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-label="Toggle Sidebar"
          >
            {isCollapsed ? <TbChevronRight size={18} /> : <TbChevronLeft size={18} />}
          </button>
        </div>

        <nav className={styles.navMenu}>
          <ul className={styles.navList}>
            {menuItems.map((item) => (
              <li key={item.path} className={styles.navItem}>
                <NavLink
                  to={item.path}
                  className={({ isActive }) =>
                    `${styles.navLink} ${isActive ? styles.active : ""}`
                  }
                  onClick={closeMobileSidebar}
                >
                  <span className={styles.icon}>{item.icon}</span>
                  {!isCollapsed && <span className={styles.label}>{item.label}</span>}
                </NavLink>
              </li>
            ))}
          </ul>
        </nav>

        <div className={styles.sidebarFooter}>
          <button
            className={`${styles.navLink} ${styles.logoutBtn}`}
            onClick={handleLogout}
          >
            <span className={styles.icon}>
              <TbLogout size={22} />
            </span>
            {!isCollapsed && <span className={styles.label}>Logout</span>}
          </button>
        </div>
      </aside>
    </>
  );
};

export default Sidebar;
