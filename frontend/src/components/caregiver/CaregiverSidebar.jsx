import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  TbLayoutDashboard,
  TbUsers,
  TbPill,
  TbCalendarTime,
  TbHistory,
  TbBell,
  TbUser,
  TbSettings,
  TbLogout,
  TbChevronLeft,
  TbChevronRight,
} from "react-icons/tb";
import Logo from "../common/Logo";
import styles from "../dashboard/Sidebar.module.css";
import { removeToken } from "../../utils/token";

const CaregiverSidebar = ({ user, isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }) => {
  const navigate = useNavigate();

  const menuItems = [
    { path: "/caregiver/dashboard", label: "Dashboard", icon: <TbLayoutDashboard size={22} /> },
    { path: "/caregiver/patients", label: "My Patients", icon: <TbUsers size={22} /> },
    { path: "/caregiver/medicines", label: "Medicines", icon: <TbPill size={22} /> },
    { path: "/caregiver/reminders", label: "Reminders", icon: <TbCalendarTime size={22} /> },
    { path: "/caregiver/history", label: "Medication History", icon: <TbHistory size={22} /> },
    { path: "/caregiver/notifications", label: "Notifications", icon: <TbBell size={22} /> },
    { path: "/caregiver/profile", label: "Profile", icon: <TbUser size={22} /> },
    { path: "/caregiver/settings", label: "Settings", icon: <TbSettings size={22} /> },
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
            <NavLink to="/caregiver/dashboard" className={styles.logoCompact}>
              <span className={styles.logoIcon}>🧑⚕️</span>
            </NavLink>
          )}

          <button
            className={styles.toggleBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-label="Toggle Caregiver Sidebar"
          >
            {isCollapsed ? <TbChevronRight size={18} /> : <TbChevronLeft size={18} />}
          </button>
        </div>

        <div className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider text-teal-600 border-b border-slate-100">
          {!isCollapsed ? "Caregiver Workspace" : "Care"}
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

export default CaregiverSidebar;
