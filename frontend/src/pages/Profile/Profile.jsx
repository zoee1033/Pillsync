import React, { useState, useEffect } from "react";
import DashboardLayout from "../../components/dashboard/DashboardLayout";
import Card from "../../components/common/Card";
import Input from "../../components/common/Input";
import Button from "../../components/common/Button";
import styles from "./Profile.module.css";
import { updateProfile, changePassword } from "../../services/profileService";
import { TbUserEdit, TbLock, TbShieldCheck } from "react-icons/tb";

const ProfileContent = ({ user, onUserUpdate }) => {
  const currentUser = user || {
    full_name: "Health User",
    role: "patient",
    email: "user@example.com",
    phone: "",
    created_at: null,
    is_active: true,
  };

  // Form State for Profile Details
  const [profileData, setProfileData] = useState({
    fullName: currentUser.full_name || "",
    phone: currentUser.phone || "",
  });

  // Synchronize state when user details load
  useEffect(() => {
    if (user) {
      setProfileData({
        fullName: user.full_name || "",
        phone: user.phone || "",
      });
    }
  }, [user]);

  const [isEditing, setIsEditing] = useState(false);
  const [profileStatus, setProfileStatus] = useState({ type: "", message: "" });
  const [profileLoading, setProfileLoading] = useState(false);

  // Form State for Password Change
  const [passwordData, setPasswordData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });
  const [passwordStatus, setPasswordStatus] = useState({ type: "", message: "" });
  const [passwordLoading, setPasswordLoading] = useState(false);

  // Password validation checks
  const validations = {
    length: passwordData.newPassword.length >= 8,
    uppercase: /[A-Z]/.test(passwordData.newPassword),
    lowercase: /[a-z]/.test(passwordData.newPassword),
    number: /[0-9]/.test(passwordData.newPassword),
    match: passwordData.newPassword && passwordData.newPassword === passwordData.confirmPassword,
  };

  const getPasswordStrength = (pass) => {
    if (!pass) return { score: 0, label: "", color: "" };
    let score = 0;
    if (pass.length >= 8) score += 1;
    if (/[A-Z]/.test(pass)) score += 1;
    if (/[a-z]/.test(pass)) score += 1;
    if (/[0-9]/.test(pass)) score += 1;

    if (score <= 1) return { score, label: "Weak", color: "#EF4444" };
    if (score <= 3) return { score, label: "Medium", color: "#F59E0B" };
    return { score, label: "Strong", color: "#10B981" };
  };

  const strength = getPasswordStrength(passwordData.newPassword);

  const getInitials = (name) => {
    if (!name) return "U";
    return name
      .split(" ")
      .map((n) => n[0])
      .slice(0, 2)
      .join("")
      .toUpperCase();
  };

  const handleProfileChange = (e) => {
    setProfileData({
      ...profileData,
      [e.target.name]: e.target.value,
    });
  };

  const handlePasswordChange = (e) => {
    setPasswordData({
      ...passwordData,
      [e.target.name]: e.target.value,
    });
  };

  const handleProfileSubmit = async (e) => {
    e.preventDefault();
    setProfileStatus({ type: "", message: "" });

    if (!profileData.fullName.trim()) {
      setProfileStatus({ type: "error", message: "Full name is required." });
      return;
    }

    try {
      setProfileLoading(true);
      const response = await updateProfile({
        full_name: profileData.fullName,
        phone: profileData.phone,
      });

      if (response && response.data) {
        onUserUpdate(response.data);
        setProfileStatus({ type: "success", message: "Profile updated successfully." });
        setIsEditing(false);
      }
    } catch (error) {
      setProfileStatus({
        type: "error",
        message: error.response?.data?.detail || "Failed to update profile.",
      });
    } finally {
      setProfileLoading(false);
    }
  };

  const handlePasswordSubmit = async (e) => {
    e.preventDefault();
    setPasswordStatus({ type: "", message: "" });

    // Validate strength criteria before calling backend
    const allValid = Object.values(validations).every(Boolean);
    if (!allValid) {
      setPasswordStatus({
        type: "error",
        message: "Please meet all password requirements before saving.",
      });
      return;
    }

    try {
      setPasswordLoading(true);
      const response = await changePassword({
        current_password: passwordData.currentPassword,
        new_password: passwordData.newPassword,
        confirm_password: passwordData.confirmPassword,
      });

      setPasswordStatus({ type: "success", message: response.message || "Password changed successfully." });
      setPasswordData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    } catch (error) {
      setPasswordStatus({
        type: "error",
        message: error.response?.data?.detail || "Failed to change password.",
      });
    } finally {
      setPasswordLoading(false);
    }
  };

  const formatDate = (dateStr) => {
    if (!dateStr) return "N/A";
    try {
      const date = new Date(dateStr);
      return date.toLocaleDateString("en-US", {
        year: "numeric",
        month: "long",
        day: "numeric",
      });
    } catch (e) {
      return "N/A";
    }
  };

  return (
    <div className={styles.profileContainer}>
      {/* Header */}
      <div className={styles.headerSection}>
        <h2 className={styles.pageTitle}>Profile Management</h2>
        <p className={styles.pageSubtitle}>Update your personal information and account security.</p>
      </div>

      <div className={styles.profileGrid}>
        {/* Left Column: Profile Card */}
        <div className={styles.leftCol}>
          <Card className={styles.avatarCard}>
            <div className={styles.avatarContainer}>
              <div className={styles.avatarLarge}>
                {getInitials(currentUser.full_name)}
              </div>
              <h3 className={styles.userName}>{currentUser.full_name}</h3>
              <span className={styles.userRoleBadge}>{currentUser.role}</span>
            </div>

            <div className={styles.accountStatus}>
              <div className={styles.statusRow}>
                <span className={styles.statusLabel}>Account Status:</span>
                <span className={styles.statusActive}>Active</span>
              </div>
              <div className={styles.statusRow}>
                <span className={styles.statusLabel}>Member Since:</span>
                <span className={styles.statusDate}>{formatDate(currentUser.created_at)}</span>
              </div>
            </div>
          </Card>
        </div>

        {/* Right Column: Profile details and Security settings */}
        <div className={styles.rightCol}>
          {/* Personal Info Card */}
          <Card className={styles.detailsCard}>
            <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}>
                <TbUserEdit className={styles.cardHeaderIcon} />
                Personal Information
              </h3>
              {!isEditing && (
                <Button
                  variant="outline"
                  onClick={() => setIsEditing(true)}
                  className={styles.editBtn}
                >
                  Edit Details
                </Button>
              )}
            </div>

            {profileStatus.message && (
              <div
                className={`${styles.alert} ${
                  profileStatus.type === "success" ? styles.alertSuccess : styles.alertError
                }`}
              >
                {profileStatus.message}
              </div>
            )}

            <form onSubmit={handleProfileSubmit} className={styles.profileForm}>
              <div className={styles.formGrid}>
                <Input
                  label="Full Name"
                  name="fullName"
                  value={profileData.fullName}
                  onChange={handleProfileChange}
                  disabled={!isEditing}
                  required
                />

                <Input
                  label="Email Address (Read-Only)"
                  name="email"
                  type="email"
                  value={currentUser.email}
                  disabled
                />

                <Input
                  label="Phone Number"
                  name="phone"
                  type="tel"
                  placeholder="+91 9876543210"
                  value={profileData.phone}
                  onChange={handleProfileChange}
                  disabled={!isEditing}
                />

                <Input
                  label="Account Role (Read-Only)"
                  name="role"
                  value={currentUser.role ? currentUser.role.toUpperCase() : "PATIENT"}
                  disabled
                />
              </div>

              {isEditing && (
                <div className={styles.formActions}>
                  <Button
                    type="button"
                    variant="outline"
                    disabled={profileLoading}
                    onClick={() => {
                      setProfileData({
                        fullName: currentUser.full_name || "",
                        phone: currentUser.phone || "",
                      });
                      setIsEditing(false);
                      setProfileStatus({ type: "", message: "" });
                    }}
                  >
                    Cancel
                  </Button>
                  <Button type="submit" variant="primary" disabled={profileLoading}>
                    {profileLoading ? "Saving..." : "Save Changes"}
                  </Button>
                </div>
              )}
            </form>
          </Card>

          {/* Change Password Card */}
          <Card className={styles.securityCard}>
            <div className={styles.cardHeader}>
              <h3 className={styles.cardTitle}>
                <TbLock className={styles.cardHeaderIcon} />
                Change Password
              </h3>
            </div>

            <p className={styles.cardDesc}>
              Update your account password regularly to keep your health data secure.
            </p>

            {passwordStatus.message && (
              <div
                className={`${styles.alert} ${
                  passwordStatus.type === "success" ? styles.alertSuccess : styles.alertError
                }`}
              >
                {passwordStatus.message}
              </div>
            )}

            <form onSubmit={handlePasswordSubmit} className={styles.passwordForm}>
              <Input
                label="Current Password"
                name="currentPassword"
                type="password"
                placeholder="Enter current password"
                value={passwordData.currentPassword}
                onChange={handlePasswordChange}
                required
              />

              <div className={styles.passwordValidationLayout}>
                <div className={styles.passwordInputs}>
                  <Input
                    label="New Password"
                    name="newPassword"
                    type="password"
                    placeholder="Enter new password"
                    value={passwordData.newPassword}
                    onChange={handlePasswordChange}
                    required
                  />

                  {passwordData.newPassword && (
                    <div className={styles.strengthIndicator}>
                      <div className={styles.strengthBarContainer}>
                        <div
                          className={styles.strengthBar}
                          style={{
                            width: `${(strength.score / 4) * 100}%`,
                            backgroundColor: strength.color,
                          }}
                        />
                      </div>
                      <span className={styles.strengthLabel} style={{ color: strength.color }}>
                        Password Strength: <strong>{strength.label}</strong>
                      </span>
                    </div>
                  )}

                  <Input
                    label="Confirm New Password"
                    name="confirmPassword"
                    type="password"
                    placeholder="Confirm new password"
                    value={passwordData.confirmPassword}
                    onChange={handlePasswordChange}
                    required
                  />
                </div>

                {/* Validation checklist card */}
                <div className={styles.checklistCard}>
                  <h5>Password Requirements:</h5>
                  <ul>
                    <li className={validations.length ? styles.valid : styles.invalid}>
                      <span>{validations.length ? "✓" : "○"}</span> At least 8 characters
                    </li>
                    <li className={validations.uppercase ? styles.valid : styles.invalid}>
                      <span>{validations.uppercase ? "✓" : "○"}</span> At least 1 uppercase letter
                    </li>
                    <li className={validations.lowercase ? styles.valid : styles.invalid}>
                      <span>{validations.lowercase ? "✓" : "○"}</span> At least 1 lowercase letter
                    </li>
                    <li className={validations.number ? styles.valid : styles.invalid}>
                      <span>{validations.number ? "✓" : "○"}</span> At least 1 number
                    </li>
                    <li className={validations.match ? styles.valid : styles.invalid}>
                      <span>{validations.match ? "✓" : "○"}</span> Passwords match
                    </li>
                  </ul>
                </div>
              </div>

              <div className={styles.passwordFormActions}>
                <Button type="submit" variant="primary" disabled={passwordLoading}>
                  {passwordLoading ? "Updating..." : "Change Password"}
                </Button>
              </div>
            </form>
          </Card>
        </div>
      </div>
    </div>
  );
};

const Profile = ({ user, onUserUpdate }) => {
  return (
    <DashboardLayout>
      <ProfileContent user={user} onUserUpdate={onUserUpdate} />
    </DashboardLayout>
  );
};

export default Profile;
