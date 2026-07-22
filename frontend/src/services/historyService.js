import api from "./api";

export const getHistory = async () => {
  const response = await api.get("/history");
  return response.data;
};

export const getHistoryById = async (historyId) => {
  const response = await api.get(`/history/${historyId}`);
  return response.data;
};

export const createHistory = async (historyData) => {
  const response = await api.post("/history", historyData);
  return response.data;
};

export const updateHistory = async (historyId, historyData) => {
  const response = await api.put(`/history/${historyId}`, historyData);
  return response.data;
};

export const deleteHistory = async (historyId) => {
  const response = await api.delete(`/history/${historyId}`);
  return response.data;
};

export const markTaken = async (historyId) => {
  const response = await api.put(`/history/${historyId}/taken`);
  return response.data;
};

export const markSkipped = async (historyId, reason) => {
  const response = await api.put(`/history/${historyId}/skipped`, null, {
    params: { reason },
  });
  return response.data;
};

export const markMissed = async (historyId) => {
  const response = await api.put(`/history/${historyId}/missed`);
  return response.data;
};
