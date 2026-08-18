import React from "react";
import { Navigate } from "react-router-dom";
import { getToken } from "../utils/token";

const ProtectedRoute = ({ children, allowedRoles }) => {
  const token = getToken();

  if (!token) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles && allowedRoles.length > 0) {
    const storedUser = localStorage.getItem("user");
    const user = storedUser ? JSON.parse(storedUser) : null;
    const userRole = (user?.role || "patient").toLowerCase();
    const allowedNormalized = allowedRoles.map((r) => r.toLowerCase());

    if (!allowedNormalized.includes(userRole)) {
      if (userRole === "caregiver") {
        return <Navigate to="/caregiver/dashboard" replace />;
      } else if (userRole === "admin") {
        return <Navigate to="/admin/dashboard" replace />;
      } else {
        return <Navigate to="/dashboard" replace />;
      }
    }
  }

  return children;
};

export default ProtectedRoute;