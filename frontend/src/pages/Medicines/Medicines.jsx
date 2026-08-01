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
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState({ type: "", text: "" });
  const [form, setForm] = useState(initialForm);
  const [editingId, setEditingId] = useState(null);

  const isFiltered = Boolean(effectiveTreatment?.id);
  const displayMedicines = medicines;
  const listLoading = loading;

  const loadMedicines = async () => {
    setLoading(true);
    setMessage({ type: "", text: "" });

    try {
      const response = effectiveTreatment?.id
        ? await getMedicinesByTreatment(effectiveTreatment.id)
        : await getAllMedicines();
      setMedicines(response || []);
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
          <div className={styles.cardHeader}>
            <h3>{isFiltered ? "Medicine List" : "All Medicines"}</h3>
          </div>

          {listLoading ? (
            <LoadingSkeleton lines={5} />
          ) : displayMedicines.length === 0 ? (
            <EmptyState
              title="No medicines found"
              message={
                isFiltered
                  ? "Add a medicine to manage it for this treatment."
                  : "No medicines exist yet. Add one from a treatment to start tracking them."
              }
              action={
                <Button variant="secondary" onClick={() => navigate("/treatments")}>Browse Treatments</Button>
              }
            />
          ) : (
            <div className={styles.medicineList}>
              {displayMedicines.map((medicine) => (
                <div key={medicine.id} className={styles.medicineItem}>
                  <div className={styles.medicineHeader}>
                    <div>
                      <div className={styles.medicineName}>{medicine.medicine_name}</div>
                      <div className={styles.medicineSubtext}>{medicine.medicine_type}</div>
                    </div>
                    <span className={medicine.is_active ? styles.statusActive : styles.statusInactive}>
                      {medicine.is_active ? "Active" : "Inactive"}
                    </span>
                  </div>

                  <div className={styles.medicineDetails}>
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Dosage</span>
                      <span>{medicine.dosage}</span>
                    </div>
                    <div className={styles.detailRow}>
                      <span className={styles.detailLabel}>Quantity</span>
                      <span>{medicine.quantity}</span>
                    </div>
                    {medicine.treatment_name && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Treatment</span>
                        <span>{medicine.treatment_name}</span>
                      </div>
                    )}
                    {medicine.instructions && (
                      <div className={styles.detailRow}>
                        <span className={styles.detailLabel}>Instructions</span>
                        <span>{medicine.instructions}</span>
                      </div>
                    )}
                  </div>

                  <div className={styles.itemActions}>
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
              ))}
            </div>
          )}
        </Card>
      </div>
    </div>
  );
};

export default Medicines;
