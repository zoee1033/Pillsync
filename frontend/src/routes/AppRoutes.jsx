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

import ProtectedRoute from "./ProtectedRoute";
import DashboardLayout from "../components/dashboard/DashboardLayout";
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

        <Route
          path="/"
          element={<Landing />}
        />

        <Route
          path="/login"
          element={<Login />}
        />

        <Route
          path="/register"
          element={<Register />}
        />

        {/* Protected Routes (layout persists) */}
        <Route
          element={
            <ProtectedRoute>
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


      </Routes>
    </Router>
  );
};

export default AppRoutes;

