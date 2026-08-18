import api from "./api";

export const getAdminDashboard = async () => {
  const response = await api.get("/admin/dashboard");
  return response.data;
};

export const getAdminUsers = async (roleFilter = "all", search = "") => {
  const params = {};
  if (roleFilter && roleFilter !== "all") params.role = roleFilter;
  if (search) params.search = search;
  const response = await api.get("/admin/users", { params });
  return response.data;
};

export const updateAdminUser = async (userId, payload) => {
  const response = await api.put(`/admin/users/${userId}`, payload);
  return response.data;
};

export const getAdminPatients = async () => {
  const response = await api.get("/admin/patients");
  return response.data;
};

export const getAdminCaregivers = async () => {
  const response = await api.get("/admin/caregivers");
  return response.data;
};

export const assignCaregiverToPatient = async (caregiverId, patientId) => {
  const response = await api.post("/admin/assign-caregiver", {
    caregiver_id: caregiverId,
    patient_id: patientId,
  });
  return response.data;
};

export const getAdminMedicines = async () => {
  const response = await api.get("/admin/medicines");
  return response.data;
};

export const getAdminTreatments = async () => {
  const response = await api.get("/admin/treatments");
  return response.data;
};

export const getAdminReminders = async () => {
  const response = await api.get("/admin/reminders");
  return response.data;
};

export const getAdminNotifications = async () => {
  const response = await api.get("/admin/notifications");
  return response.data;
};

export const getAdminAnalytics = async () => {
  const response = await api.get("/admin/analytics");
  return response.data;
};

export const getAdminActivity = async () => {
  const response = await api.get("/admin/activity");
  return response.data;
};
