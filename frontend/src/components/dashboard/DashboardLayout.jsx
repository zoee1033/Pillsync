import React, { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import styles from "./DashboardLayout.module.css";
import { getProfile } from "../../services/profileService";

const DashboardLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  // 1. Maintain authenticated user React state (Single Source of Truth)
  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  // 2. Fetch fresh user details on mount
  useEffect(() => {
    const loadUserProfile = async () => {
      try {
        const response = await getProfile();
        if (response && response.data) {
          setUser(response.data);
          localStorage.setItem("user", JSON.stringify(response.data));
        }
      } catch (error) {
        console.error("Failed to load user profile in layout:", error);
      }
    };

    loadUserProfile();
  }, []);

  const handleUserUpdate = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("user", JSON.stringify(updatedUser));
  };

  return (
    <div className={styles.layout}>
      <Sidebar
        user={user}
        isCollapsed={isCollapsed}
        setIsCollapsed={setIsCollapsed}
        isMobileOpen={isMobileOpen}
        setIsMobileOpen={setIsMobileOpen}
      />
      
      <div
        className={`${styles.mainContent} ${
          isCollapsed ? styles.collapsedMain : ""
        }`}
      >
        <Navbar user={user} onMenuClick={() => setIsMobileOpen(true)} />
        <main className={styles.contentBody}>
          <div className={styles.container}>
            <Outlet context={{ user, onUserUpdate: handleUserUpdate }} />
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
