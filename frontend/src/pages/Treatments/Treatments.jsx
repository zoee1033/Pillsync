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
      const data = Array.isArray(response) ? response : (response?.data && Array.isArray(response.data) ? response.data : []);
      setTreatments(data);
    } catch (error) {
      console.error(error);
      setMessage({ type: "error", text: "Unable to load treatments." });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadTreatments();

    const handleGlobalRefresh = () => {
      loadTreatments();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
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
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
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
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (error) {
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to delete treatment.",
      });
    }
  };

  const [selectedDetailsTreatment, setSelectedDetailsTreatment] = useState(null);

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
                <option value="Paused">Paused</option>
                <option value="Completed">Completed</option>
                <option value="Archived">Archived</option>
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
              {treatments.map((item) => {
                const startMs = new Date(item.start_date).getTime();
                const endMs = new Date(item.end_date).getTime();
                const nowMs = new Date().getTime();
                const totalMs = Math.max(1, endMs - startMs);
                const elapsedMs = Math.max(0, nowMs - startMs);
                const progressPct = Math.min(100, Math.max(0, Math.round((elapsedMs / totalMs) * 100)));

                return (
                  <div key={item.id} className={styles.treatmentItem}>
                    <div className={styles.treatmentInfo} style={{ width: "100%" }}>
                      <div className="flex items-center justify-between">
                        <div className={styles.treatmentTitle}>{item.disease_name}</div>
                        <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          item.status === 'Active' ? 'bg-green-100 text-green-800' :
                          item.status === 'Completed' ? 'bg-blue-100 text-blue-800' :
                          item.status === 'Paused' ? 'bg-amber-100 text-amber-800' : 'bg-slate-100 text-slate-800'
                        }`}>
                          {item.status}
                        </span>
                      </div>

                      {item.doctor_name && (
                        <div className="text-xs text-slate-500 mt-1">
                          Doctor: <strong className="text-slate-700">{item.doctor_name}</strong>
                        </div>
                      )}

                      {/* Progress Bar */}
                      <div className="mt-3 flex items-center gap-3">
                        <div className="flex-1 bg-slate-200 rounded-full h-2 overflow-hidden">
                          <div
                            className="bg-[#0F8B6D] h-2 rounded-full transition-all duration-500"
                            style={{ width: `${progressPct}%` }}
                          />
                        </div>
                        <span className="text-xs font-semibold text-slate-600 min-w-[36px] text-right">{progressPct}%</span>
                      </div>
                    </div>

                    <div className={styles.itemActions} style={{ marginTop: "1rem" }}>
                      <Button variant="outline" onClick={() => setSelectedDetailsTreatment(item)}>
                        View Details
                      </Button>
                      <Button variant="outline" onClick={() => handleEdit(item)}>
                        Edit
                      </Button>
                      <Button variant="secondary" onClick={() => openMedicines(item)}>
                        Manage Medicines
                      </Button>
                      <Button variant="outline" onClick={() => handleDelete(item.id)}>
                        Delete
                      </Button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </Card>
      </div>

      {/* View Details Modal */}
      {selectedDetailsTreatment && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-xl max-w-lg w-full p-6 relative border border-slate-100">
            <button
              onClick={() => setSelectedDetailsTreatment(null)}
              className="absolute top-4 right-4 text-slate-400 hover:text-slate-600 text-lg font-bold"
            >
              ✕
            </button>
            <h3 className="text-xl font-bold text-slate-800 mb-1">{selectedDetailsTreatment.disease_name}</h3>
            <div className="flex items-center gap-2 mb-4">
              <span className={`px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                selectedDetailsTreatment.status === 'Active' ? 'bg-emerald-100 text-emerald-800' :
                selectedDetailsTreatment.status === 'Completed' ? 'bg-teal-100 text-teal-800' : 'bg-slate-100 text-slate-800'
              }`}>
                {selectedDetailsTreatment.status}
              </span>
            </div>

            <div className="space-y-3 text-sm text-slate-600 border-t border-slate-100 pt-3">
              {selectedDetailsTreatment.doctor_name && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Doctor:</span>
                  <span className="font-semibold text-slate-800">{selectedDetailsTreatment.doctor_name}</span>
                </div>
              )}
              {selectedDetailsTreatment.diagnosis_date && (
                <div className="flex justify-between">
                  <span className="text-slate-400">Diagnosis Date:</span>
                  <span>{String(selectedDetailsTreatment.diagnosis_date).slice(0, 10)}</span>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-400">Start Date:</span>
                <span>{String(selectedDetailsTreatment.start_date).slice(0, 10)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">End Date:</span>
                <span>{String(selectedDetailsTreatment.end_date).slice(0, 10)}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Days Remaining:</span>
                <span className="font-semibold text-[#0F8B6D]">
                  {Math.max(0, Math.ceil((new Date(selectedDetailsTreatment.end_date).getTime() - new Date().getTime()) / (1000 * 60 * 60 * 24)))} days
                </span>
              </div>
              {selectedDetailsTreatment.notes && (
                <div className="border-t border-slate-100 pt-2 mt-2">
                  <span className="text-slate-400 block mb-1">Notes:</span>
                  <p className="bg-slate-50 p-2.5 rounded-lg text-slate-700 text-xs italic">{selectedDetailsTreatment.notes}</p>
                </div>
              )}
            </div>

            <div className="mt-6 flex justify-end gap-2">
              <Button variant="secondary" onClick={() => {
                const item = selectedDetailsTreatment;
                setSelectedDetailsTreatment(null);
                openMedicines(item);
              }}>
                Medicines & Reminders
              </Button>
              <Button variant="outline" onClick={() => setSelectedDetailsTreatment(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Treatments;
