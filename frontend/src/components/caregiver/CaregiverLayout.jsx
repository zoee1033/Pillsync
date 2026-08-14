import React, { useState, useEffect } from "react";
import { Outlet } from "react-router-dom";
import CaregiverSidebar from "./CaregiverSidebar";
import Navbar from "../dashboard/Navbar";
import styles from "../dashboard/DashboardLayout.module.css";
import { getProfile } from "../../services/profileService";

const CaregiverLayout = () => {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const [user, setUser] = useState(() => {
    const savedUser = localStorage.getItem("user");
    return savedUser ? JSON.parse(savedUser) : null;
  });

  useEffect(() => {
    const loadUserProfile = async () => {
      try {
        const response = await getProfile();
        const userObj = response?.data || response;
        if (userObj && (userObj.id || userObj.email || userObj.full_name)) {
          setUser(userObj);
          localStorage.setItem("user", JSON.stringify(userObj));
        }
      } catch (error) {
        console.error("Failed to load caregiver user profile:", error);
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
      <CaregiverSidebar
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

export default CaregiverLayout;
