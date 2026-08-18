import api from "./api";

export const getCaregiverDashboard = async () => {
  const response = await api.get("/caregiver/dashboard");
  return response.data;
};

export const getCaregiverPatients = async () => {
  const response = await api.get("/caregiver/patients");
  return response.data;
};

export const getCaregiverPatientDetail = async (patientId) => {
  const response = await api.get(`/caregiver/patients/${patientId}`);
  return response.data;
};

export const linkPatientByEmail = async (patientEmail) => {
  const response = await api.post("/caregiver/link-patient", { patient_email: patientEmail });
  return response.data;
};

export const getCaregiverMedicines = async () => {
  const response = await api.get("/caregiver/medicines");
  return response.data;
};

export const getCaregiverReminders = async () => {
  const response = await api.get("/caregiver/reminders");
  return response.data;
};

export const getCaregiverHistory = async () => {
  const response = await api.get("/caregiver/history");
  return response.data;
};

export const getCaregiverNotifications = async () => {
  const response = await api.get("/caregiver/notifications");
  return response.data;
};

export const getPendingPatientRequests = async () => {
  const response = await api.get("/caregiver/patient-requests");
  return response.data;
};

export const getMyCaregiver = async () => {
  const response = await api.get("/caregiver/my-caregiver");
  return response.data;
};

export const acceptCaregiverRequest = async (requestId) => {
  const response = await api.post(`/caregiver/requests/${requestId}/accept`);
  return response.data;
};

export const rejectCaregiverRequest = async (requestId) => {
  const response = await api.post(`/caregiver/requests/${requestId}/reject`);
  return response.data;
};
