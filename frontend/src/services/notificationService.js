import api from "./api";

export const getNotifications = async () => {
  const response = await api.get("/notifications");
  return response.data;
};

export const markNotificationRead = async (notificationId) => {
  const response = await api.put(`/notifications/${notificationId}/read`);
  return response.data;
};

export const deleteNotification = async (notificationId) => {
  const response = await api.delete(`/notifications/${notificationId}`);
  return response.data;
};

export const performNotificationAction = async (notificationId, actionType) => {
  const response = await api.put(`/notifications/${notificationId}/action`, null, {
    params: { action_type: actionType },
  });
  return response.data;
};

export const performReminderAction = async (reminderId, actionType) => {
  const response = await api.put(`/notifications/reminder/${reminderId}/action`, null, {
    params: { action_type: actionType },
  });
  return response.data;
};
