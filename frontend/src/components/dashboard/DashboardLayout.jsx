import React, { useState, useEffect } from "react";
import Sidebar from "./Sidebar";
import Navbar from "./Navbar";
import styles from "./DashboardLayout.module.css";
import { getProfile } from "../../services/profileService";

const DashboardLayout = ({ children }) => {
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

  // 3. Clone children and inject user + onUserUpdate props
  const childrenWithProps = React.Children.map(children, (child) => {
    if (React.isValidElement(child)) {
      return React.cloneElement(child, {
        user,
        onUserUpdate: handleUserUpdate,
      });
    }
    return child;
  });

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
            {childrenWithProps}
          </div>
        </main>
      </div>
    </div>
  );
};

export default DashboardLayout;
