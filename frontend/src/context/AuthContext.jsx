import React, { createContext, useEffect, useMemo, useState } from "react";
import { getToken, removeToken, saveToken } from "../utils/token";
import { getProfile } from "../services/profileService";
import { loginUser } from "../services/authService";

const AuthContext = createContext({
  user: null,
  loading: true,
  isAuthenticated: false,
  login: async () => {},
  logout: () => {},
  updateUser: () => {},
  refreshUser: async () => {},
});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(() => {
    const storedUser = localStorage.getItem("user");
    return storedUser ? JSON.parse(storedUser) : null;
  });
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(Boolean(getToken()));

  useEffect(() => {
    const loadSession = async () => {
      const token = getToken();
      if (!token) {
        setLoading(false);
        return;
      }

      try {
        const profile = await getProfile();
        setUser(profile);
        localStorage.setItem("user", JSON.stringify(profile));
        setIsAuthenticated(true);
      } catch (error) {
        removeToken();
        localStorage.removeItem("user");
        setUser(null);
        setIsAuthenticated(false);
      } finally {
        setLoading(false);
      }
    };

    loadSession();
  }, []);

  const refreshUser = async () => {
    try {
      const profile = await getProfile();
      setUser(profile);
      localStorage.setItem("user", JSON.stringify(profile));
      return profile;
    } catch (error) {
      return null;
    }
  };

  const login = async (credentials) => {
    const response = await loginUser(credentials);

    if (response?.access_token) {
      saveToken(response.access_token);
      setIsAuthenticated(true);
    }

    if (response?.user) {
      setUser(response.user);
      localStorage.setItem("user", JSON.stringify(response.user));
    }

    return response;
  };

  const logout = () => {
    removeToken();
    localStorage.removeItem("user");
    setUser(null);
    setIsAuthenticated(false);
  };

  const updateUser = (updatedUser) => {
    setUser(updatedUser);
    localStorage.setItem("user", JSON.stringify(updatedUser));
  };

  const value = useMemo(
    () => ({
      user,
      loading,
      isAuthenticated,
      login,
      logout,
      updateUser,
      refreshUser,
    }),
    [user, loading, isAuthenticated],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export default AuthContext;
