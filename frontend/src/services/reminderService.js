import api from "./api";

export const getRemindersByMedicine = async (medicineId) => {
  const response = await api.get(`/reminders/medicine/${medicineId}`);
  return response.data;
};

export const createReminder = async (reminderData) => {
  const response = await api.post("/reminders", reminderData);
  return response.data;
};

export const updateReminder = async (reminderId, reminderData) => {
  const response = await api.put(`/reminders/${reminderId}`, reminderData);
  return response.data;
};

export const deleteReminder = async (reminderId) => {
  const response = await api.delete(`/reminders/${reminderId}`);
  return response.data;
};

export const snoozeReminder = async (reminderId, minutes) => {
  const response = await api.put(`/reminders/${reminderId}/snooze`, null, {
    params: { minutes },
  });
  return response.data;
};
