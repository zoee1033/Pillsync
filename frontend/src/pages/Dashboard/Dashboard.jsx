import React from "react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import { Link } from "react-router-dom";
import {
  TbUser,
  TbSettings,
  TbActivity,
  TbCalendarEvent,
  TbAlertCircle,
} from "react-icons/tb";
import styles from "./Dashboard.module.css";

const DashboardContent = ({ user }) => {
  // Fallback user details
  const currentUser = user || {
    full_name: "Health User",
    role: "patient",
    email: "user@example.com",
    phone: "",
  };

  // Current Date
  const currentDate = new Date().toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });

  return (
    <div className={styles.dashboardContainer}>
      {/* Welcome Section */}
      <div className={styles.headerSection}>
        <h2 className={styles.pageTitle}>Dashboard Overview</h2>
        <span className={styles.dateText}>{currentDate}</span>
      </div>

      {/* Dashboard Grid */}
      <div className={styles.grid}>
        {/* 1. Welcome Card */}
        <Card className={`${styles.card} ${styles.welcomeCard}`}>
          <div className={styles.welcomeInfo}>
            <span className={styles.emoji}>👋</span>
            <div>
              <h3 className={styles.cardTitle}>Welcome Back, {currentUser.full_name}!</h3>
              <p className={styles.cardText}>
                Your health dashboard is up-to-date. Keep track of your medication schedule and settings here.
              </p>
            </div>
          </div>
          <div className={styles.statusBanner}>
            <TbAlertCircle size={20} className={styles.statusIcon} />
            <span>Milestone 1 Active: Currently running in foundation mode.</span>
          </div>
        </Card>

        {/* 2. Quick Actions Card */}
        <Card className={`${styles.card} ${styles.quickActionsCard}`}>
          <h3 className={styles.cardTitle}>Quick Actions</h3>
          <div className={styles.actionGrid}>
            <Link to="/profile" className={styles.actionLink}>
              <Button variant="outline" className={styles.actionBtn}>
                <TbUser size={18} />
                <span>View Profile</span>
              </Button>
            </Link>
            <Link to="/settings" className={styles.actionLink}>
              <Button variant="outline" className={styles.actionBtn}>
                <TbSettings size={18} />
                <span>App Settings</span>
              </Button>
            </Link>
          </div>
        </Card>

        {/* 3. Profile Summary Card */}
        <Card className={`${styles.card} ${styles.profileCard}`}>
          <h3 className={styles.cardTitle}>Profile Summary</h3>
          <div className={styles.profileDetails}>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Email:</span>
              <span className={styles.detailValue}>{currentUser.email}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Role:</span>
              <span className={`${styles.roleText} ${styles[currentUser.role?.toLowerCase() || "patient"]}`}>
                {currentUser.role}
              </span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Phone:</span>
              <span className={styles.detailValue}>{currentUser.phone || "Not Set"}</span>
            </div>
            <div className={styles.detailRow}>
              <span className={styles.detailLabel}>Status:</span>
              <span className={styles.statusActive}>Active</span>
            </div>
          </div>
        </Card>

        {/* 4. Recent Activity Card */}
        <Card className={`${styles.card} ${styles.activityCard}`}>
          <h3 className={styles.cardTitle}>Recent Activity</h3>
          <div className={styles.activityList}>
            <div className={styles.activityItem}>
              <div className={styles.activityIcon}>
                <TbActivity size={16} />
              </div>
              <div className={styles.activityDetails}>
                <p className={styles.activityDesc}>Logged in securely to PillSync</p>
                <span className={styles.activityTime}>Just now</span>
              </div>
            </div>
            <div className={styles.activityItem}>
              <div className={styles.activityIcon}>
                <TbCalendarEvent size={16} />
              </div>
              <div className={styles.activityDetails}>
                <p className={styles.activityDesc}>Dashboard initialized for Milestone 1</p>
                <span className={styles.activityTime}>Recently</span>
              </div>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
};

const Dashboard = () => {
  return (
    <DashboardLayout>
      <DashboardContent />
    </DashboardLayout>
  );
};

export default Dashboard;