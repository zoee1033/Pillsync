import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import styles from "./Treatments.module.css";
import {
  getTreatments,
  createTreatment,
  updateTreatment,
  deleteTreatment,
} from "../../services/treatmentService";

const initialForm = {
  disease_name: "",
  doctor_name: "",
  diagnosis_date: "",
  start_date: "",
  end_date: "",
  status: "Active",
  notes: "",
};

const Treatments = () => {
  const [treatments, setTreatments] = useState([]);
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });

  const loadTreatments = async () => {
    setLoading(true);
    try {
      const response = await getTreatments();
      setTreatments(response);
    } catch (error) {
      console.error(error);
      setMessage({ type: "error", text: "Unable to load treatments." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTreatments();
  }, []);

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setMessage({ type: "", text: "" });
  };

  const handleChange = (e) => {
    setForm({
      ...form,
      [e.target.name]: e.target.value,
    });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSaving(true);
    setMessage({ type: "", text: "" });

    try {
      if (editingId) {
        await updateTreatment(editingId, form);
        setMessage({ type: "success", text: "Treatment updated successfully." });
      } else {
        await createTreatment(form);
        setMessage({ type: "success", text: "Treatment created successfully." });
      }
      resetForm();
      await loadTreatments();
    } catch (error) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to save treatment.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (item) => {
    setEditingId(item.id);
    setForm({
      disease_name: item.disease_name || "",
      doctor_name: item.doctor_name || "",
      diagnosis_date: item.diagnosis_date ? item.diagnosis_date.slice(0, 10) : "",
      start_date: item.start_date ? item.start_date.slice(0, 10) : "",
      end_date: item.end_date ? item.end_date.slice(0, 10) : "",
      status: item.status || "Active",
      notes: item.notes || "",
    });
    setMessage({ type: "", text: "" });
  };

  const navigate = useNavigate();

  const openMedicines = (item) => {
    navigate("/medicines", { state: { treatment: item } });
  };

  const handleViewHistory = (item) => {
    navigate(`/history?treatment_id=${item.id}`, {
      state: { treatment: item },
    });
  };

  const handleDelete = async (id) => {
    try {
      await deleteTreatment(id);
      setMessage({ type: "success", text: "Treatment deleted successfully." });
      await loadTreatments();
    } catch (error) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to delete treatment.",
      });
    }
  };

  return (
    <div className={styles.treatmentContainer}>
      <div className={styles.headerSection}>
        <h2 className={styles.pageTitle}>Treatments</h2>
        <p className={styles.pageSubtitle}>Manage your treatment plans and track care details.</p>
      </div>

      <div className={styles.contentGrid}>
        <Card className={styles.formCard}>
          <div className={styles.cardHeader}>
            <h3>{editingId ? "Edit Treatment" : "Create Treatment"}</h3>
          </div>

          {message.text && (
            <div className={`${styles.alert} ${message.type === "success" ? styles.alertSuccess : styles.alertError}`}>
              {message.text}
            </div>
          )}

          <form onSubmit={handleSubmit} className={styles.treatmentForm}>
            <Input
              label="Disease Name"
              name="disease_name"
              value={form.disease_name}
              onChange={handleChange}
              required
            />

            <Input
              label="Doctor Name"
              name="doctor_name"
              value={form.doctor_name}
              onChange={handleChange}
            />

            <Input
              label="Diagnosis Date"
              name="diagnosis_date"
              type="date"
              value={form.diagnosis_date}
              onChange={handleChange}
            />

            <Input
              label="Start Date"
              name="start_date"
              type="date"
              value={form.start_date}
              onChange={handleChange}
              required
            />

            <Input
              label="End Date"
              name="end_date"
              type="date"
              value={form.end_date}
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
              >
                <option value="Active">Active</option>
                <option value="Completed">Completed</option>
                <option value="Cancelled">Cancelled</option>
              </select>
            </div>

            <div className={styles.textareaRow}>
              <label className={styles.inputLabel}>Notes</label>
              <textarea
                name="notes"
                value={form.notes}
                onChange={handleChange}
                className={styles.textarea}
                rows={4}
                placeholder="Add treatment notes"
              />
            </div>

            <div className={styles.actionRow}>
              <Button type="submit" variant="primary" disabled={saving}>
                {saving ? "Saving..." : editingId ? "Update Treatment" : "Create Treatment"}
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
            <h3>Treatment Plans</h3>
          </div>

          {loading ? (
            <p>Loading treatments...</p>
          ) : treatments.length === 0 ? (
            <p>No treatments found.</p>
          ) : (
            <div className={styles.treatmentList}>
              {treatments.map((item) => (
                <div key={item.id} className={styles.treatmentItem}>
                  <div className={styles.treatmentInfo}>
                    <div className={styles.treatmentTitle}>{item.disease_name}</div>
                    <div className={styles.treatmentMeta}>
                      <span>{item.status}</span>
                      <span>{item.start_date}</span>
                    </div>
                  </div>
                  <div className={styles.itemActions}>
                    <Button variant="outline" onClick={() => handleEdit(item)}>
                      Edit
                    </Button>
                    <Button variant="secondary" onClick={() => openMedicines(item)}>
                      Manage Medicines
                    </Button>
                    <Button variant="outline" onClick={() => handleViewHistory(item)}>
                      View History
                    </Button>
                    <Button variant="outline" onClick={() => handleDelete(item.id)}>
                      Delete
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Treatments;
