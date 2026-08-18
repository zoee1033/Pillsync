import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  useSearchParams,
} from "react-router-dom";

import Landing from "../pages/Landing/Landing";
import Login from "../pages/Auth/Login";
import Register from "../pages/Auth/Register";

// Patient Pages
import Dashboard from "../pages/Dashboard/Dashboard";
import Profile from "../pages/Profile/Profile";
import Settings from "../pages/Settings/Settings";
import Treatments from "../pages/Treatments/Treatments";
import Medicines from "../pages/Medicines/Medicines";
import Reminders from "../pages/Reminders/Reminders";
import History from "../pages/History/History";
import Notifications from "../pages/Notifications/Notifications";
import OCR from "../pages/OCR/OCR";
import Analytics from "../pages/Analytics/Analytics";

// Caregiver Pages
import CaregiverDashboard from "../pages/Caregiver/CaregiverDashboard";
import CaregiverPatients from "../pages/Caregiver/CaregiverPatients";
import CaregiverPatientDetail from "../pages/Caregiver/CaregiverPatientDetail";
import CaregiverMedicines from "../pages/Caregiver/CaregiverMedicines";
import CaregiverReminders from "../pages/Caregiver/CaregiverReminders";
import CaregiverHistory from "../pages/Caregiver/CaregiverHistory";
import CaregiverNotifications from "../pages/Caregiver/CaregiverNotifications";
import CaregiverProfile from "../pages/Caregiver/CaregiverProfile";
import CaregiverSettings from "../pages/Caregiver/CaregiverSettings";

// Admin Pages
import AdminDashboard from "../pages/Admin/AdminDashboard";
import AdminUsers from "../pages/Admin/AdminUsers";
import AdminPatients from "../pages/Admin/AdminPatients";
import AdminCaregivers from "../pages/Admin/AdminCaregivers";
import AdminMedicines from "../pages/Admin/AdminMedicines";
import AdminTreatments from "../pages/Admin/AdminTreatments";
import AdminReminders from "../pages/Admin/AdminReminders";
import AdminNotifications from "../pages/Admin/AdminNotifications";
import AdminAnalytics from "../pages/Admin/AdminAnalytics";
import AdminActivity from "../pages/Admin/AdminActivity";
import AdminSettings from "../pages/Admin/AdminSettings";

// Layouts & Guards
import ProtectedRoute from "./ProtectedRoute";
import DashboardLayout from "../components/dashboard/DashboardLayout";
import CaregiverLayout from "../components/caregiver/CaregiverLayout";
import AdminLayout from "../components/admin/AdminLayout";
import NotificationDetailsModal from "../components/notifications/NotificationDetailsModal";

const NotificationModalContainer = () => {
  const [searchParams, setSearchParams] = useSearchParams();
  const reminderId = searchParams.get("open_reminder_id");

  if (!reminderId) return null;

  const handleClose = () => {
    searchParams.delete("open_reminder_id");
    setSearchParams(searchParams, { replace: true });
  };

  const handleRefresh = () => {
    window.dispatchEvent(new Event("pillsync_refresh_ui"));
  };

  return (
    <NotificationDetailsModal
      reminderId={reminderId}
      onClose={handleClose}
      onRefresh={handleRefresh}
    />
  );
};

const AppRoutes = () => {
  return (
    <Router>
      <NotificationModalContainer />
      <Routes>

        {/* Public Routes */}
        <Route path="/" element={<Landing />} />
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />

        {/* Patient Protected Routes */}
        <Route
          element={
            <ProtectedRoute allowedRoles={["patient"]}>
              <DashboardLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/ocr" element={<OCR />} />
          <Route path="/analytics" element={<Analytics />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/treatments" element={<Treatments />} />
          <Route path="/medicines" element={<Medicines />} />
          <Route path="/reminders" element={<Reminders />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/history" element={<History />} />
          <Route path="/settings" element={<Settings />} />
        </Route>

        {/* Caregiver Protected Routes */}
        <Route
          element={
            <ProtectedRoute allowedRoles={["caregiver", "admin"]}>
              <CaregiverLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/caregiver/dashboard" element={<CaregiverDashboard />} />
          <Route path="/caregiver/patients" element={<CaregiverPatients />} />
          <Route path="/caregiver/patients/:patientId" element={<CaregiverPatientDetail />} />
          <Route path="/caregiver/medicines" element={<CaregiverMedicines />} />
          <Route path="/caregiver/reminders" element={<CaregiverReminders />} />
          <Route path="/caregiver/history" element={<CaregiverHistory />} />
          <Route path="/caregiver/notifications" element={<CaregiverNotifications />} />
          <Route path="/caregiver/profile" element={<CaregiverProfile />} />
          <Route path="/caregiver/settings" element={<CaregiverSettings />} />
        </Route>

        {/* Admin Protected Routes */}
        <Route
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminLayout />
            </ProtectedRoute>
          }
        >
          <Route path="/admin/dashboard" element={<AdminDashboard />} />
          <Route path="/admin/users" element={<AdminUsers />} />
          <Route path="/admin/patients" element={<AdminPatients />} />
          <Route path="/admin/caregivers" element={<AdminCaregivers />} />
          <Route path="/admin/medicines" element={<AdminMedicines />} />
          <Route path="/admin/treatments" element={<AdminTreatments />} />
          <Route path="/admin/reminders" element={<AdminReminders />} />
          <Route path="/admin/notifications" element={<AdminNotifications />} />
          <Route path="/admin/analytics" element={<AdminAnalytics />} />
          <Route path="/admin/activity" element={<AdminActivity />} />
          <Route path="/admin/settings" element={<AdminSettings />} />
        </Route>

      </Routes>
    </Router>
  );
};

export default AppRoutes;
