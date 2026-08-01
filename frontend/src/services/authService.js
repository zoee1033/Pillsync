import api from "./api";

export const registerUser = async (userData) => {
  const response = await api.post("/auth/register", userData);
  return response.data;
};

export const loginUser = async (credentials) => {
  const response = await api.post("/auth/login", credentials);
  return response.data;
};

export const requestForgotPasswordOTP = async (email) => {
  const response = await api.post("/auth/forgot-password/request", { email });
  return response.data;
};

export const verifyForgotPasswordOTP = async (email, otp) => {
  const response = await api.post("/auth/forgot-password/verify-otp", { email, otp });
  return response.data;
};

export const resetPasswordWithOTP = async ({ email, otp, new_password, confirm_password }) => {
  const response = await api.post("/auth/forgot-password/reset", {
    email,
    otp,
    new_password,
    confirm_password,
  });
  return response.data;
};

export const googleLogin = async (payload) => {
  const response = await api.post("/auth/google", payload);
  return response.data;
};

export const appleLogin = async (payload) => {
  const response = await api.post("/auth/apple", payload);
  return response.data;
};