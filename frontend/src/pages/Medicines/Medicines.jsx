import React, { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import Card from "../../components/common/Card";
import Button from "../../components/common/Button";
import Input from "../../components/common/Input";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSkeleton from "../../components/ui/LoadingSkeleton";
import {
  getAllMedicines,
  getMedicinesByTreatment,
  createMedicine,
  updateMedicine,
  deleteMedicine,
} from "../../services/medicineService";
import DosageAnalysisModal from "../../components/medicines/DosageAnalysisModal";
import styles from "./Medicines.module.css";

const initialForm = {
  medicine_name: "",
  medicine_type: "Tablet",
  dosage: "",
  quantity: 1,
  instructions: "",
  is_active: true,
};

const MedicineTypes = [
  "Tablet",
  "Capsule",
  "Syrup",
  "Injection",
  "Drops",
  "Ointment",
  "Inhaler",
  "Other",
];

const Medicines = ({ treatment }) => {
  const location = useLocation();
  const navigate = useNavigate();
  const routeState = location.state || {};
  const effectiveTreatment = treatment || routeState.treatment;

  const [medicines, setMedicines] = useState([]);
  const [predictionsMap, setPredictionsMap] = useState({});
  const [statusFilter, setStatusFilter] = useState(routeState.filterStatus || "All");
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);
  const [analysisMedicineId, setAnalysisMedicineId] = useState(null);

  const isFiltered = Boolean(effectiveTreatment?.id);

  const loadMedicines = async () => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      let medsList = [];
      if (effectiveTreatment?.id) {
        try {
          medsList = await getMedicinesByTreatment(effectiveTreatment.id);
        } catch (tErr) {
          console.warn("Treatment specific fetch failed, falling back to all user medicines:", tErr);
          medsList = await getAllMedicines();
        }
      } else {
        medsList = await getAllMedicines();
      }

      setMedicines(medsList || []);

      try {
        const predRes = await api.get("/medicines/refill-predictions");
        if (Array.isArray(predRes.data)) {
          const pMap = {};
          predRes.data.forEach((p) => {
            pMap[p.medicine_id] = p;
          });
          setPredictionsMap(pMap);
        }
      } catch (pErr) {
        console.warn("Refill predictions load warning:", pErr);
      }
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to load medicines.",
      });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadMedicines();
    setForm(initialForm);
    setEditingId(null);

    const handleGlobalRefresh = () => {
      loadMedicines();
    };

    window.addEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    return () => {
      window.removeEventListener("pillsync_refresh_ui", handleGlobalRefresh);
    };
  }, [effectiveTreatment?.id]);

  const handleQuickRestock = async (medicine) => {
    const newQtyStr = window.prompt(`Enter new stock quantity for ${medicine.medicine_name}:`, (medicine.quantity || 0) + 30);
    if (!newQtyStr) return;
    const newQty = parseInt(newQtyStr);
    if (isNaN(newQty) || newQty <= 0) {
      alert("Please enter a valid stock quantity greater than 0.");
      return;
    }
    try {
      await updateMedicine(medicine.id, { quantity: newQty });
      setMessage({ type: "success", text: `Stock updated to ${newQty} tablets for ${medicine.medicine_name}.` });
      await loadMedicines();
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (err) {
      alert("Failed to update stock: " + (err.response?.data?.detail || err.message));
    }
  };

  const filteredMedicines = medicines.filter((m) => {
    if (statusFilter === "All") return true;
    const pred = predictionsMap[m.id];
    if (!pred) return true;
    if (statusFilter === "Refill Soon" && (pred.status_category === "Refill Soon" || pred.status_category === "Urgent")) return true;
    return pred.status_category === statusFilter;
  });

  const displayMedicines = filteredMedicines;
  const listLoading = loading;

  const resetForm = () => {
    setForm(initialForm);
    setEditingId(null);
    setMessage({ type: "", text: "" });
  };

  const handleChange = (event) => {
    const { name, value, type, checked } = event.target;

    setForm((prev) => ({
      ...prev,
      [name]: type === "checkbox" ? checked : name === "quantity" ? Number(value) : value,
    }));
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!form.medicine_name.trim()) {
      setMessage({ type: "error", text: "Medicine name is required." });
      return;
    }

    if (!form.medicine_type) {
      setMessage({ type: "error", text: "Medicine type is required." });
      return;
    }

    if (!form.dosage.trim()) {
      setMessage({ type: "error", text: "Dosage is required." });
      return;
    }

    if (!form.quantity || form.quantity <= 0) {
      setMessage({ type: "error", text: "Quantity must be greater than zero." });
      return;
    }

    setSaving(true);
    setMessage({ type: "", text: "" });

    if (!effectiveTreatment?.id) {
      setMessage({ type: "error", text: "Choose a treatment before creating a medicine." });
      setSaving(false);
      return;
    }

    try {
      if (editingId) {
        await updateMedicine(editingId, {
          medicine_name: form.medicine_name.trim(),
          medicine_type: form.medicine_type,
          dosage: form.dosage.trim(),
          quantity: form.quantity,
          instructions: form.instructions.trim() || null,
          is_active: form.is_active,
        });
        setMessage({ type: "success", text: "Medicine updated successfully." });
      } else {
        await createMedicine({
          treatment_id: effectiveTreatment.id,
          medicine_name: form.medicine_name.trim(),
          medicine_type: form.medicine_type,
          dosage: form.dosage.trim(),
          quantity: form.quantity,
          instructions: form.instructions.trim() || null,
          is_active: form.is_active,
        });
        setMessage({ type: "success", text: "Medicine created successfully." });
      }
      resetForm();
      await loadMedicines();
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Failed to save medicine.",
      });
    } finally {
      setSaving(false);
    }
  };

  const handleEdit = (medicine) => {
    setEditingId(medicine.id);
    setForm({
      medicine_name: medicine.medicine_name || "",
      medicine_type: medicine.medicine_type || "Tablet",
      dosage: medicine.dosage || "",
      quantity: medicine.quantity || 1,
      instructions: medicine.instructions || "",
      is_active: medicine.is_active ?? true,
    });
    setMessage({ type: "", text: "" });
  };

  const handleDelete = async (medicineId) => {
    const confirmed = window.confirm("Delete this medicine? This action cannot be undone.");
    if (!confirmed) {
      return;
    }

    try {
      await deleteMedicine(medicineId);
      setMessage({ type: "success", text: "Medicine deleted successfully." });
      await loadMedicines();
      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));
    } catch (error) {
      console.error(error);
      setMessage({
        type: "error",
        text: error.response?.data?.detail || "Unable to delete medicine.",
      });
    }
  };

  const openReminders = (medicine) => {
    navigate("/reminders", { state: { medicine, treatment: effectiveTreatment } });
  };

  const clearFilter = () => {
    navigate("/medicines");
  };

  return (
    <div className={styles.medicinePage}>
      <div className={styles.pageHeader}>
        <div>
          <h2 className={styles.pageTitle}>Medicines</h2>
          <p className={styles.pageSubtitle}>
            {isFiltered
              ? "Manage medicines for this treatment plan."
              : "View all medicines across your treatments."}
          </p>
        </div>
      </div>

      {isFiltered && (
        <Card className={styles.filterBanner}>
          <div>
            <div className={styles.filterTitle}>Showing medicines for:</div>
            <div className={styles.filterValue}>{effectiveTreatment.disease_name}</div>
          </div>
          <Button variant="outline" onClick={clearFilter}>
            Clear Filter
          </Button>
        </Card>
      )}

      {isFiltered && (
        <Card className={styles.treatmentCard}>
          <div className={styles.cardHeader}>
            <h3 className={styles.treatmentHeading}>Treatment</h3>
            <span className={styles.treatmentStatus}>{effectiveTreatment.status || "Active"}</span>
          </div>
          <div className={styles.treatmentDetails}>
            <div>
              <div className={styles.detailLabel}>Name</div>
              <div className={styles.detailValue}>{effectiveTreatment.disease_name}</div>
            </div>
            <div>
              <div className={styles.detailLabel}>Doctor</div>
              <div className={styles.detailValue}>{effectiveTreatment.doctor_name || "—"}</div>
            </div>
            <div>
              <div className={styles.detailLabel}>Duration</div>
              <div className={styles.detailValue}>
                {effectiveTreatment.start_date} - {effectiveTreatment.end_date}
              </div>
            </div>
          </div>
        </Card>
      )}

      <div className={styles.gridLayout}>
        {isFiltered && (
          <Card className={styles.formCard}>
            <div className={styles.cardHeader}>
              <h3>{editingId ? "Edit Medicine" : "Add Medicine"}</h3>
            </div>

            {message.text && (
              <div className={`${styles.alert} ${message.type === "success" ? styles.alertSuccess : styles.alertError}`}>
                {message.text}
              </div>
            )}

            <form onSubmit={handleSubmit} className={styles.form}>
              <Input
                label="Medicine Name"
                name="medicine_name"
                value={form.medicine_name}
                onChange={handleChange}
                required
              />

              <div className={styles.selectRow}>
                <label className={styles.selectLabel}>Medicine Type</label>
                <select
                  name="medicine_type"
                  value={form.medicine_type}
                  onChange={handleChange}
                  className={styles.selectField}
                  required
                >
                  {MedicineTypes.map((type) => (
                    <option key={type} value={type}>
                      {type}
                    </option>
                  ))}
                </select>
              </div>

              <Input
                label="Dosage"
                name="dosage"
                value={form.dosage}
                onChange={handleChange}
                required
              />

              <Input
                label="Quantity"
                name="quantity"
                type="number"
                min="1"
                value={form.quantity}
                onChange={handleChange}
                required
              />

              <div className={styles.textareaRow}>
                <label className={styles.inputLabel}>Instructions</label>
                <textarea
                  name="instructions"
                  value={form.instructions}
                  onChange={handleChange}
                  className={styles.textarea}
                  rows={4}
                  placeholder="Add medicine instructions"
                />
              </div>

              <label className={styles.checkboxRow}>
                <input
                  type="checkbox"
                  name="is_active"
                  checked={form.is_active}
                  onChange={handleChange}
                />
                <span>Active</span>
              </label>

              <div className={styles.buttonRow}>
                <Button type="submit" variant="primary" disabled={saving}>
                  {saving ? "Saving..." : editingId ? "Update Medicine" : "Create Medicine"}
                </Button>
                {editingId && (
                  <Button type="button" variant="outline" onClick={resetForm}>
                    Cancel
                  </Button>
                )}
              </div>
            </form>
          </Card>
        )}

        <Card className={styles.listCard}>
          <div className={styles.cardHeader} style={{ flexWrap: "wrap", gap: "0.5rem" }}>
            <h3>{isFiltered ? "Medicine List" : "All Medicines"}</h3>
            <div style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}>
              {["All", "Healthy", "Refill Soon", "Critical"].map((st) => (
                <button
                  key={st}
                  onClick={() => setStatusFilter(st)}
                  style={{
                    padding: "0.25rem 0.65rem",
                    borderRadius: "20px",
                    fontSize: "0.78rem",
                    fontWeight: 700,
                    cursor: "pointer",
                    border: statusFilter === st ? "2px solid #0F8B6D" : "1px solid #cbd5e1",
                    backgroundColor: statusFilter === st ? "#E6F4F0" : "#ffffff",
                    color: statusFilter === st ? "#0F8B6D" : "#475569"
                  }}
                >
                  {st === "Healthy" ? "🟢 Healthy" : st === "Refill Soon" ? "🟡 Needs Refill" : st === "Critical" ? "🔴 Critical" : "All"}
                </button>
              ))}
            </div>
          </div>

          {listLoading ? (
            <LoadingSkeleton lines={5} />
          ) : displayMedicines.length === 0 ? (
            <EmptyState
              title="No medicines found"
              message={
                isFiltered
                  ? "Add a medicine to manage it for this treatment."
                  : "No medicines match the selected filter criteria."
              }
              action={
                <Button variant="secondary" onClick={() => { setStatusFilter("All"); navigate("/treatments"); }}>Browse Treatments</Button>
              }
            />
          ) : (
            <div className={styles.medicineList}>
              {displayMedicines.map((medicine) => {
                const pred = predictionsMap[medicine.id] || {
                  status_category: "Healthy",
                  badge_icon: "🟢",
                  hex_color: "#10B981",
                  remaining_days: 30,
                  daily_consumption: 1,
                  refill_date: "N/A",
                  progress_percent: 100
                };

                return (
                  <div key={medicine.id} className={styles.medicineItem}>
                    <div className={styles.medicineHeader}>
                      <div>
                        <div className={styles.medicineName}>
                          {medicine.medicine_name}
                        </div>
                        <div className={styles.medicineSubtext}>{medicine.medicine_type} • Dosage: {medicine.dosage}</div>
                      </div>
                      <div style={{ display: "flex", gap: "0.4rem", alignItems: "center" }}>
                        <span
                          style={{
                            padding: "0.2rem 0.6rem",
                            borderRadius: "20px",
                            fontSize: "0.75rem",
                            fontWeight: 700,
                            backgroundColor: `${pred.hex_color}18`,
                            color: pred.hex_color,
                            border: `1px solid ${pred.hex_color}40`
                          }}
                        >
                          {pred.badge_icon} {pred.status_category} ({pred.remaining_days} Days Left)
                        </span>
                        <span className={medicine.is_active ? styles.statusActive : styles.statusInactive}>
                          {medicine.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                    </div>

                    <div className={styles.medicineDetails}>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Current Stock</span>
                        <span style={{ fontWeight: 700 }}>{medicine.quantity} Tablets</span>
                      </div>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Daily Usage</span>
                        <span style={{ fontWeight: 700 }}>{pred.daily_consumption || 1} / day</span>
                      </div>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Days Remaining</span>
                        <span style={{ fontWeight: 700, color: pred.hex_color }}>{pred.remaining_days} Days</span>
                      </div>
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Refill Before</span>
                        <span style={{ fontWeight: 700 }}>{pred.refill_date || pred.refill_recommended_date}</span>
                      </div>
                    </div>

                    {/* Smart Progress Bar */}
                    <div style={{ width: "100%", height: "8px", backgroundColor: "#e2e8f0", borderRadius: "6px", overflow: "hidden", margin: "0.6rem 0" }}>
                      <div
                        style={{
                          height: "100%",
                          width: `${pred.progress_percent || Math.min(100, Math.max(5, (pred.remaining_days / 30) * 100))}%`,
                          backgroundColor: pred.hex_color || "#10b981",
                          borderRadius: "6px",
                          transition: "width 0.3s ease"
                        }}
                      ></div>
                    </div>

                    <div className={styles.itemActions}>
                      <Button variant="primary" onClick={() => handleQuickRestock(medicine)}>
                        + Restock Stock
                      </Button>
                      <Button variant="outline" onClick={() => setAnalysisMedicineId(medicine.id)}>
                        Dosage Analysis
                      </Button>
                      <Button variant="outline" onClick={() => handleEdit(medicine)}>
                        Edit
                      </Button>
                      <Button variant="secondary" onClick={() => openReminders(medicine)}>
                        Manage Reminders
                      </Button>
                      <Button variant="outline" onClick={() => handleDelete(medicine.id)}>
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

      {analysisMedicineId && (
        <DosageAnalysisModal
          medicineId={analysisMedicineId}
          onClose={() => setAnalysisMedicineId(null)}
        />
      )}
    </div>
  );
};

export default Medicines;

