import api from "./api";

export const getTreatments = async () => {
  const response = await api.get("/treatments");
  return response.data;
};

export const createTreatment = async (treatmentData) => {
  const response = await api.post("/treatments", treatmentData);
  return response.data;
};

export const updateTreatment = async (treatmentId, treatmentData) => {
  const response = await api.put(`/treatments/${treatmentId}`, treatmentData);
  return response.data;
};

export const deleteTreatment = async (treatmentId) => {
  const response = await api.delete(`/treatments/${treatmentId}`);
  return response.data;
};
