import api from "./api";

/**
 * Fetch current user profile details from backend.
 */
export const getProfile = async () => {
  const response = await api.get("/profile/me");
  return response.data?.data || response.data;
};

/**
 * Update user full name and phone number on the backend.
 */
export const updateProfile = async (profileData) => {
  const response = await api.put("/profile/update", profileData);
  return response.data;
};

/**
 * Change authenticated user password on the backend.
 */
export const changePassword = async (passwordData) => {
  const response = await api.put("/profile/change-password", passwordData);
  return response.data;
};
