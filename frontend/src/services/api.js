import axios from "axios";
import { getToken, removeToken } from "../utils/token";

const api = axios.create({
  baseURL: "http://127.0.0.1:8000",
  headers: {
    "Content-Type": "application/json",
  },
});

// Automatically inject JWT access token into headers for every request
api.interceptors.request.use(
  (config) => {
    const token = getToken();
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      const isNotificationPolling = error.config?.url?.includes("/notifications/unread");
      if (!isNotificationPolling) {
        removeToken();
        localStorage.removeItem("user");
      }
    }
    return Promise.reject(error);
  }
);

export default api;