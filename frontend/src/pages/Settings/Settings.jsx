import React, { useState } from "react";
import useAuth from "../../hooks/useAuth";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import styles from "./Settings.module.css";
import {
  TbBell,
  TbShield,
  TbLanguage,
  TbHelp,
  TbSun,
  TbMoon,
  TbDeviceMobile,
} from "react-icons/tb";

const SettingsContent = () => {
  const { user } = useAuth();
  const [notifications, setNotifications] = useState({
    emailAlerts: true,
    reminderPush: true,
    refillAlerts: false,
  });

  const [language, setLanguage] = useState("english");

  const handleToggle = (key) => {
    setNotifications((prev) => ({
      ...prev,
      [key]: !prev[key],
    }));
  };

  return (
    <div className={styles.settingsContainer}>
      {/* Header */}
      <div className={styles.headerSection}>
        <h2 className={styles.pageTitle}>Account Settings</h2>
        <p className={styles.pageSubtitle}>Manage your preferences and configurations.</p>
      </div>

      <div className={styles.settingsGrid}>
        {/* 1. Notifications Panel */}
        <Card className={styles.settingsCard}>
          <h3 className={styles.cardTitle}>
            <TbBell className={styles.iconGreen} />
            Notification Settings
          </h3>
          <p className={styles.cardDesc}>Choose how you want to be reminded of your doses.</p>

          <div className={styles.optionsList}>
            <div className={styles.optionItem}>
              <div className={styles.optionDetails}>
                <h4>Email Alerts</h4>
                <p>Receive summaries of your weekly progress and alerts via email.</p>
              </div>
              <label className={styles.switch}>
                <input
                  type="checkbox"
                  checked={notifications.emailAlerts}
                  onChange={() => handleToggle("emailAlerts")}
                />
                <span className={styles.slider} />
              </label>
            </div>

            <div className={styles.optionItem}>
              <div className={styles.optionDetails}>
                <h4>Smart Push Notifications</h4>
                <p>Get push alerts on your desktop or mobile before taking medications.</p>
              </div>
              <label className={styles.switch}>
                <input
                  type="checkbox"
                  checked={notifications.reminderPush}
                  onChange={() => handleToggle("reminderPush")}
                />
                <span className={styles.slider} />
              </label>
            </div>

            <div className={styles.optionItem}>
              <div className={styles.optionDetails}>
                <h4>Refill Reminders</h4>
                <p>Alert me when a medicine's inventory level falls below the threshold.</p>
              </div>
              <label className={styles.switch}>
                <input
                  type="checkbox"
                  checked={notifications.refillAlerts}
                  onChange={() => handleToggle("refillAlerts")}
                />
                <span className={styles.slider} />
              </label>
            </div>
          </div>
        </Card>

        {/* 2. Theme & Localization Panel */}
        <Card className={styles.settingsCard}>
          <h3 className={styles.cardTitle}>
            <TbLanguage className={styles.iconGreen} />
            Display & Language
          </h3>
          <p className={styles.cardDesc}>Configure application display language and theme.</p>

          <div className={styles.themeSelectorSection}>
            <h4>Theme Preference</h4>
            <div className={styles.themeOptions}>
              <div className={`${styles.themeBox} ${styles.themeActive}`}>
                <TbSun size={20} />
                <span>Light (Active)</span>
              </div>
              <div className={`${styles.themeBox} ${styles.themeDisabled}`}>
                <TbMoon size={20} />
                <span>Dark (Premium)</span>
              </div>
            </div>
          </div>

          <div className={styles.selectSection}>
            <label htmlFor="language-select" className={styles.selectLabel}>
              Application Language
            </label>
            <select
              id="language-select"
              className={styles.dropdown}
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
            >
              <option value="english">English (US)</option>
              <option value="hindi">Hindi (India)</option>
              <option value="spanish">Spanish</option>
              <option value="french">French</option>
            </select>
          </div>
        </Card>

        {/* 3. Help & Support */}
        <Card className={`${styles.settingsCard} ${styles.spanTwoColumns}`}>
          <h3 className={styles.cardTitle}>
            <TbHelp className={styles.iconGreen} />
            Support & Documentation
          </h3>
          <p className={styles.cardDesc}>Need assistance? Browse resources or contact support.</p>
          
          <div className={styles.supportContainer}>
            <div className={styles.supportBox}>
              <TbShield className={styles.supportIcon} />
              <div>
                <h4>Privacy & Security Policy</h4>
                <p>Read about how we securely encrypt and backup your health records.</p>
              </div>
            </div>

            <div className={styles.supportBox}>
              <TbDeviceMobile className={styles.supportIcon} />
              <div>
                <h4>Sync mobile application</h4>
                <p>Connect PillSync IoT smart pillbox devices to your online profile.</p>
              </div>
            </div>
          </div>

          <div className={styles.supportFooter}>
            <Button variant="outline" className={styles.supportBtn}>
              Frequently Asked Questions
            </Button>
            <Button variant="primary" className={styles.supportBtn}>
              Contact Support Desk
            </Button>
          </div>
        </Card>
      </div>
    </div>
  );
};

export default SettingsContent;
