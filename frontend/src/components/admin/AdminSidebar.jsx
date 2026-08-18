import React from "react";
import { NavLink, useNavigate } from "react-router-dom";
import {
  TbLayoutDashboard,
  TbUsers,
  TbUserCheck,
  TbUserHeart,
  TbPill,
  TbClipboardList,
  TbCalendarTime,
  TbBell,
  TbChartBar,
  TbActivity,
  TbSettings,
  TbLogout,
  TbChevronLeft,
  TbChevronRight,
} from "react-icons/tb";
import Logo from "../common/Logo";
import styles from "../dashboard/Sidebar.module.css";
import { removeToken } from "../../utils/token";

const AdminSidebar = ({ user, isCollapsed, setIsCollapsed, isMobileOpen, setIsMobileOpen }) => {
  const navigate = useNavigate();

  const menuItems = [
    { path: "/admin/dashboard", label: "Dashboard", icon: <TbLayoutDashboard size={22} /> },
    { path: "/admin/users", label: "Users", icon: <TbUsers size={22} /> },
    { path: "/admin/patients", label: "Patients", icon: <TbUserHeart size={22} /> },
    { path: "/admin/caregivers", label: "Caregivers", icon: <TbUserCheck size={22} /> },
    { path: "/admin/medicines", label: "Medicines", icon: <TbPill size={22} /> },
    { path: "/admin/treatments", label: "Treatments", icon: <TbClipboardList size={22} /> },
    { path: "/admin/reminders", label: "Reminders", icon: <TbCalendarTime size={22} /> },
    { path: "/admin/notifications", label: "Notifications", icon: <TbBell size={22} /> },
    { path: "/admin/analytics", label: "Analytics", icon: <TbChartBar size={22} /> },
    { path: "/admin/activity", label: "Activity Feed", icon: <TbActivity size={22} /> },
    { path: "/admin/settings", label: "Settings", icon: <TbSettings size={22} /> },
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
            <NavLink to="/admin/dashboard" className={styles.logoCompact}>
              <span className={styles.logoIcon}>👑</span>
            </NavLink>
          )}

          <button
            className={styles.toggleBtn}
            onClick={() => setIsCollapsed(!isCollapsed)}
            aria-label="Toggle Admin Sidebar"
          >
            {isCollapsed ? <TbChevronRight size={18} /> : <TbChevronLeft size={18} />}
          </button>
        </div>

        <div className="px-4 py-2 text-[11px] font-bold uppercase tracking-wider text-purple-600 border-b border-slate-100">
          {!isCollapsed ? "Platform Admin" : "Admin"}
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

export default AdminSidebar;
