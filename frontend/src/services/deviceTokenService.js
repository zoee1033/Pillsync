import api from "./api";

export const registerDeviceToken = async (payload) => {
  const response = await api.post("/device-tokens/", payload);
  return response.data;
};
