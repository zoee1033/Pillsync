import api from "./api";

export const getAllMedicines = async () => {
  const response = await api.get("/medicines");
  return response.data;
};

export const getMedicinesByTreatment = async (treatmentId) => {
  const response = await api.get(`/medicines/treatment/${treatmentId}`);
  return response.data;
};

export const createMedicine = async (medicineData) => {
  const response = await api.post("/medicines", medicineData);
  return response.data;
};

export const updateMedicine = async (medicineId, medicineData) => {
  const response = await api.put(`/medicines/${medicineId}`, medicineData);
  return response.data;
};

export const deleteMedicine = async (medicineId) => {
  const response = await api.delete(`/medicines/${medicineId}`);
  return response.data;
};
