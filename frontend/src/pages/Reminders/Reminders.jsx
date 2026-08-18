import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSkeleton from "../../components/ui/LoadingSkeleton";
import {
  getAllReminders,
  getRemindersByMedicine,
  createReminder,
  updateReminder,
  deleteReminder,
  snoozeReminder,
} from "../../services/reminderService";
import styles from "./Reminders.module.css";

const initialForm = {
  reminder_time: "",
  repeat_type: "Daily",
  notification_enabled: true,
  snooze_minutes: 10,
  status: "Active",
};

const repeatOptions = ["Daily", "Weekly", "Monthly", "Custom"];
const statusOptions = ["Active", "Paused", "Completed"];

const Reminders = ({ medicine, treatment }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const routeState = location.state || {};
  const effectiveMedicine = medicine || routeState.medicine;
  const effectiveTreatment = treatment || routeState.treatment;
  const isFiltered = Boolean(effectiveMedicine?.id);

  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);

  const loadReminders = async () => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      const response = effectiveMedicine?.id
        ? await getRemindersByMedicine(effectiveMedicine.id)
        : await getAllReminders();
      setReminders(response || []);
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to load reminders.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadReminders();
    setForm(initialForm);
    setEditingId(null);
  }, [effectiveMedicine?.id]);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setMessage({ type: "", text: "" });
  };

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;
    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : name === "snooze_minutes" ? Number(value) : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!editingId && !effectiveMedicine?.id) {
      setMessage({ type: "error", text: "Select a medicine before adding reminders." });
      return;
    }

    if (!form.reminder_time) {
      setMessage({ type: "error", text: "Reminder time is required." });
      return;
    }

    if (!repeatOptions.includes(form.repeat_type)) {
      setMessage({ type: "error", text: "Repeat type is invalid." });
      return;
    }

    if (!statusOptions.includes(form.status)) {
      setMessage({ type: "error", text: "Status is invalid." });
      return;
    }

    if (!form.snooze_minutes || form.snooze_minutes < 5 || form.snooze_minutes > 60) {
      setMessage({ type: "error", text: "Snooze minutes must be 5 to 60." });
      return;
    }

    setSaving(true);
    setMessage({ type: "", text: "" });

    try {
      if (editingId) {
        await updateReminder(editingId, {
          reminder_time: form.reminder_time,
          repeat_type: form.repeat_type,
          notification_enabled: form.notification_enabled,
          snooze_minutes: form.snooze_minutes,
          status: form.status,
        });
        setMessage({ type: "success", text: "Reminder updated successfully." });
      } else {
        await createReminder({
          medicine_id: effectiveMedicine.id,
          reminder_time: form.reminder_time,
          repeat_type: form.repeat_type,
          notification_enabled: form.notification_enabled,
          snooze_minutes: form.snooze_minutes,
          status: form.status,
        });
        setMessage({ type: "success", text: "Reminder created successfully." });
      }
      resetForm();
      await loadReminders();
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to save reminder.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (reminder) => {
    setEditingId(reminder.id);
    setForm({
      reminder_time: reminder.reminder_time || "",
      repeat_type: reminder.repeat_type || "Daily",
      notification_enabled: reminder.notification_enabled ?? true,
      snooze_minutes: reminder.snooze_minutes ?? 10,
      status: reminder.status || "Active",
    });
    setMessage({ type: "", text: "" });
    setTimeout(() => {
      document.getElementById("reminder-form")?.scrollIntoView({ behavior: "smooth" });
    }, 50);
  };

  const handleDelete = async (reminderId) => {
    const confirmed = window.confirm("Delete this reminder? This action cannot be undone.");
    if (!confirmed) {
      return;
    }

    try {
      await deleteReminder(reminderId);
      setMessage({ type: "success", text: "Reminder deleted successfully." });
      await loadReminders();
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to delete reminder.",
      });
    }
  };

  const handleSnooze = async (reminderId) => {
    try {
      await snoozeReminder(reminderId, 10);
      setMessage({ type: "success", text: "Reminder snoozed by 10 minutes." });
      await loadReminders();
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to snooze reminder.",
      });
    }
  };

  const handleViewHistory = (reminder) => {
    navigate(`/history?reminder_id=${reminder.id}`, {
      state: { reminder, medicine: effectiveMedicine, treatment: effectiveTreatment },
    });
  };

  const clearFilter = () => {
    navigate("/reminders");
  };

  const scrollToForm = () => {
    document.getElementById("reminder-form")?.scrollIntoView({ behavior: "smooth" });
  };

  return (
    <div className={styles.reminderPage}>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.pageTitle}>Reminders</h2>
          <p className={styles.pageSubtitle}>
            {isFiltered
              ? `Manage reminders for ${effectiveMedicine.medicine_name}.`
              : "View all reminders across your medicines."}
          </p>
        </div>
      </div>

      {isFiltered && (
        <Card className={styles.filterBanner}>
          <div>
            <div className={styles.filterTitle}>Showing reminders for:</div>
            <div className={styles.filterValue}>{effectiveMedicine.medicine_name}</div>
          </div>
          <Button variant="outline" onClick={clearFilter}>
            Clear Filter
          </Button>
        </Card>
      )}

      {!isFiltered && !editingId ? (
        <Card className={styles.listCard}>
          <div className={styles.cardHeader}>
            <h3>All Reminders</h3>
          </div>

          {loading ? (
            <LoadingSkeleton lines={5} />
          ) : reminders.length === 0 ? (
            <EmptyState
              title="No reminders yet"
              message="Create reminders from a selected medicine to start tracking them here."
              action={
                <Button variant="secondary" onClick={() => navigate("/medicines")}>
                  Browse Medicines
                </Button>
              }
            />
          ) : (
            <div className={styles.reminderList}>
              {reminders.map((reminder) => (
                <div key={reminder.id} className={styles.reminderItem}>
                  <div className={styles.reminderHeader}>
                    <div>
                      <div className={styles.reminderTime}>{reminder.reminder_time}</div>
                      <div className={styles.reminderMeta}>{reminder.repeat_type}</div>
                    </div>
                    <span className={styles.reminderStatus}>{reminder.status}</span>
                  </div>

                  <div className={styles.reminderDetails}>
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Notification</span>
                      <span>{reminder.notification_enabled ? "Enabled" : "Disabled"}</span>
                    </div>
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Snooze</span>
                      <span>{reminder.snooze_minutes} min</span>
                    </div>
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Next Reminder</span>
                      <span>{reminder.next_trigger_at ? new Date(reminder.next_trigger_at).toLocaleString() : "—"}</span>
                    </div>
                  </div>

                  <div className={styles.itemActions}>
                    <Button variant="outline" onClick={() => handleEdit(reminder)}>
                      Edit
                    </Button>
                    <Button variant="outline" onClick={() => handleSnooze(reminder.id)}>
                      Snooze
                    </Button>
                    <Button variant="outline" onClick={() => handleViewHistory(reminder)}>
                      View History
                    </Button>
                    <Button variant="secondary" onClick={() => handleDelete(reminder.id)}>
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      ) : (
        <>
          {isFiltered && effectiveMedicine && (
            <Card className={styles.medicineCard}>
              <div className={styles.cardHeader}>
                <h3>Medicine</h3>
                <span className={effectiveMedicine.is_active ? styles.statusActive : styles.statusInactive}>
                  {effectiveMedicine.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              <div className={styles.medicineDetails}>
                <div>
                  <div className={styles.detailLabel}>Name</div>
                  <div className={styles.detailValue}>{effectiveMedicine.medicine_name}</div>
                </div>
                <div>
                  <div className={styles.detailLabel}>Dosage</div>
                  <div className={styles.detailValue}>{effectiveMedicine.dosage}</div>
                </div>
                <div>
                  <div className={styles.detailLabel}>Quantity</div>
                  <div className={styles.detailValue}>{effectiveMedicine.quantity}</div>
                </div>
              </div>
            </Card>
          )}

          <div className={styles.gridLayout}>
            <Card className={styles.formCard}>
              <div className={styles.cardHeader}>
                <h3>{editingId ? "Edit Reminder" : "Add Reminder"}</h3>
              </div>

              {message.text && (
                <div className={`${styles.alert} ${message.type === "success" ? styles.alertSuccess : styles.alertError}`}>
                  {message.text}
                </div>
              )}

              <form id="reminder-form" onSubmit={handleSubmit} className={styles.form}>
                <Input
                  label="Reminder Time"
                  name="reminder_time"
                  type="time"
                  value={form.reminder_time}
                  onChange={handleChange}
                  required
                />

                <div className={styles.selectRow}>
                  <label className={styles.selectLabel}>Frequency</label>
                  <select
                    name="repeat_type"
                    value={form.repeat_type}
                    onChange={handleChange}
                    className={styles.selectField}
                    required
                  >
                    {repeatOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>

                <label className={styles.checkboxRow}>
                  <input
                    type="checkbox"
                    name="notification_enabled"
                    checked={form.notification_enabled}
                    onChange={handleChange}
                  />
                  <span>Notification enabled</span>
                </label>

                <Input
                  label="Snooze Minutes"
                  name="snooze_minutes"
                  type="number"
                  min="5"
                  max="60"
                  value={form.snooze_minutes}
                  onChange={handleChange}
                  required
                />

                <div className={styles.selectRow}>
                  <label className={styles.selectLabel}>Status</label>
                  <select
                    name="status"
                    value={form.status}
                    onChange={handleChange}
                    className={styles.selectField}
                    required
                  >
                    {statusOptions.map((option) => (
                      <option key={option} value={option}>
                        {option}
                      </option>
                    ))}
                  </select>
                </div>

                <div className={styles.buttonRow}>
                  <Button type="submit" variant="primary" disabled={saving}>
                    {saving ? "Saving..." : editingId ? "Update Reminder" : "Create Reminder"}
                  </Button>
                  {editingId && (
                    <Button type="button" variant="outline" onClick={resetForm}>
                      Cancel
                    </Button>
                  )}
                </div>
              </form>
            </Card>

            <Card className={styles.listCard}>
              <div className={styles.cardHeader}>
                <h3>Reminder List</h3>
              </div>

              {loading ? (
                <LoadingSkeleton lines={5} />
              ) : reminders.length === 0 ? (
                <EmptyState
                  title="No reminders yet"
                  message="Add a reminder to manage notifications for this medicine."
                  action={
                    <Button variant="secondary" onClick={scrollToForm}>
                      Add Reminder
                    </Button>
                  }
                />
              ) : (
                <div className={styles.reminderList}>
                  {reminders.map((reminder) => (
                    <div key={reminder.id} className={styles.reminderItem}>
                      <div className={styles.reminderHeader}>
                        <div>
                          <div className={styles.reminderTime}>{reminder.reminder_time}</div>
                          <div className={styles.reminderMeta}>{reminder.repeat_type}</div>
                        </div>
                        <span className={styles.reminderStatus}>{reminder.status}</span>
                      </div>

                      <div className={styles.reminderDetails}>
                        <div className={styles.detailRow}>
                          <span className={styles.detailLabel}>Notification</span>
                          <span>{reminder.notification_enabled ? "Enabled" : "Disabled"}</span>
                        </div>
                        <div className={styles.detailRow}>
                          <span className={styles.detailLabel}>Snooze</span>
                          <span>{reminder.snooze_minutes} min</span>
                        </div>
                        <div className={styles.detailRow}>
                          <span className={styles.detailLabel}>Next Reminder</span>
                          <span>{reminder.next_trigger_at ? new Date(reminder.next_trigger_at).toLocaleString() : "—"}</span>
                        </div>
                      </div>

                      <div className={styles.itemActions}>
                        <Button variant="outline" onClick={() => handleEdit(reminder)}>
                          Edit
                        </Button>
                        <Button variant="outline" onClick={() => handleSnooze(reminder.id)}>
                          Snooze
                        </Button>
                        <Button variant="outline" onClick={() => handleViewHistory(reminder)}>
                          View History
                        </Button>
                        <Button variant="secondary" onClick={() => handleDelete(reminder.id)}>
                          Delete
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </Card>
          </div>
        </>
      )}
    </div>
  );
};

export default Reminders;
