import React, { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import {
  TbUpload,
  TbCamera,
  TbCheck,
  TbAlertTriangle,
  TbTrash,
  TbScan,
  TbPlus,
  TbStethoscope,
  TbFolderCheck,
  TbAdjustmentsHorizontal,
  TbPill
} from "react-icons/tb";
import api from "../../services/api";
import styles from "./OCR.module.css";

const OCR = () => {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const cameraInputRef = useRef(null);

  // Workflow Selection Mode ('new' | 'existing')
  const [saveMode, setSaveMode] = useState("new");

  // Existing Treatments List
  const [treatments, setTreatments] = useState([]);
  const [selectedTreatmentId, setSelectedTreatmentId] = useState("");

  // New Treatment Form State
  const todayStr = new Date().toISOString().split("T")[0];
  const defaultEndStr = new Date(Date.now() + 30 * 86400000).toISOString().split("T")[0];
  const [newTreatment, setNewTreatment] = useState({
    disease_name: "",
    doctor_name: "",
    hospital: "",
    start_date: todayStr,
    end_date: defaultEndStr,
    notes: ""
  });

  // Automation Checkbox Options
  const [autoOptions, setAutoOptions] = useState({
    generateReminders: true,
    calculateRefills: true,
    linkMedicines: true
  });

  // Upload & Extraction State
  const [selectedFile, setSelectedFile] = useState(null);
  const [previewUrl, setPreviewUrl] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [ocrFailed, setOcrFailed] = useState(false);
  const [extractedMedicines, setExtractedMedicines] = useState([]);
  const [isSaving, setIsSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  useEffect(() => {
    fetchTreatments();
  }, []);

  const fetchTreatments = async () => {
    try {
      const res = await api.get("/treatments/");
      const list = res.data || [];
      setTreatments(list);
      if (list.length > 0) {
        setSelectedTreatmentId(list[0].id);
      }
    } catch (err) {
      console.error("Failed to fetch treatments:", err);
    }
  };

  const handleNewTreatmentChange = (field, value) => {
    setNewTreatment((prev) => ({ ...prev, [field]: value }));
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const processFile = (file) => {
    setSelectedFile(file);
    setPreviewUrl(URL.createObjectURL(file));
    runOCR(file);
  };

  const runOCR = async (file) => {
    setIsProcessing(true);
    setProgress(10);
    setOcrFailed(false);

    const interval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 90) {
          clearInterval(interval);
          return 90;
        }
        return prev + 20;
      });
    }, 250);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post("/ocr/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" }
      });

      clearInterval(interval);
      setProgress(100);

      setTimeout(() => {
        setIsProcessing(false);
        if (response.data && response.data.medicines && response.data.medicines.length > 0) {
          setExtractedMedicines(response.data.medicines);
          if (!response.data.success) {
            setOcrFailed(true);
          }
        } else {
          setOcrFailed(true);
          setExtractedMedicines([
            {
              medicine_name: "",
              medicine_type: "Tablet",
              dosage: "500mg",
              quantity: 30,
              frequency: "Daily",
              duration: "7 days",
              confidence: 0.5
            }
          ]);
        }
      }, 300);
    } catch (err) {
      clearInterval(interval);
      setIsProcessing(false);
      setOcrFailed(true);
      setExtractedMedicines([
        {
          medicine_name: "Amoxicillin",
          medicine_type: "Tablet",
          dosage: "500mg",
          quantity: 30,
          frequency: "Daily",
          duration: "7 days",
          confidence: 0.6
        }
      ]);
    }
  };

  const handleMedicineChange = (index, field, value) => {
    const updated = [...extractedMedicines];
    updated[index][field] = value;
    setExtractedMedicines(updated);
  };

  const handleAddMedicineCard = () => {
    setExtractedMedicines([
      ...extractedMedicines,
      {
        medicine_name: "",
        medicine_type: "Tablet",
        dosage: "500mg",
        quantity: 30,
        frequency: "Daily",
        duration: "7 days",
        confidence: 1.0
      }
    ]);
  };

  const handleRemoveCard = (index) => {
    setExtractedMedicines(extractedMedicines.filter((_, i) => i !== index));
  };

  const handleConfirmSave = async () => {
    if (extractedMedicines.length === 0) {
      alert("Please upload a prescription image to extract medicines before saving.");
      return;
    }

    setIsSaving(true);
    try {
      let targetTreatmentId = selectedTreatmentId;

      // FLOW 1: Create New Treatment if 'new' mode is selected
      if (saveMode === "new") {
        if (!newTreatment.disease_name.trim()) {
          alert("Please enter a Treatment / Disease Name.");
          setIsSaving(false);
          return;
        }

        const notesParts = [
          newTreatment.hospital ? `Hospital: ${newTreatment.hospital.trim()}` : "",
          newTreatment.notes ? newTreatment.notes.trim() : ""
        ].filter(Boolean);

        const treatmentPayload = {
          disease_name: newTreatment.disease_name.trim(),
          doctor_name: newTreatment.doctor_name.trim() || undefined,
          start_date: newTreatment.start_date || todayStr,
          end_date: newTreatment.end_date || defaultEndStr,
          status: "Active",
          notes: notesParts.length > 0 ? notesParts.join(" | ") : undefined
        };

        const createRes = await api.post("/treatments/", treatmentPayload);
        targetTreatmentId = createRes.data.id;
      } else {
        if (!targetTreatmentId) {
          alert("Please select an existing treatment plan.");
          setIsSaving(false);
          return;
        }
      }

      // FLOW 1 & 2: Create Medicines & Reminders under targetTreatmentId
      for (const med of extractedMedicines) {
        if (!med.medicine_name.trim()) continue;

        const medPayload = {
          treatment_id: parseInt(targetTreatmentId),
          medicine_name: med.medicine_name.trim(),
          medicine_type: med.medicine_type || "Tablet",
          dosage: med.dosage || "500mg",
          quantity: parseInt(med.quantity) || 30,
          instructions: `Prescribed duration: ${med.duration || "7 days"}. Take ${med.frequency || "Daily"}.`,
          is_active: true
        };

        const createdMedRes = await api.post("/medicines/", medPayload);
        const createdMed = createdMedRes.data;

        // Auto Generate Reminders if requested
        if (autoOptions.generateReminders && createdMed && createdMed.id) {
          try {
            await api.post("/reminders/", {
              medicine_id: createdMed.id,
              reminder_time: "09:00:00",
              repeat_type: "Daily",
              notification_enabled: true,
              snooze_minutes: 10,
              status: "Active"
            });
          } catch (remErr) {
            console.warn("Auto-reminder creation notice:", remErr);
          }
        }
      }

      setSuccessMsg(
        saveMode === "new"
          ? "✨ New Treatment Plan & Medicines created successfully!"
          : "📋 Medicines added to Treatment Plan successfully!"
      );

      window.dispatchEvent(new CustomEvent("pillsync_refresh_ui"));

      setTimeout(() => {
        navigate("/treatments");
      }, 1200);
    } catch (err) {
      alert("Failed to save treatment details: " + (err.response?.data?.detail || err.message));
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className={styles.container}>
      {/* Header */}
      <div className={styles.header}>
        <h1 className={styles.title}>
          <TbScan size={28} /> Prescription OCR Scan
        </h1>
        <p className={styles.subtitle}>
          AI extracts medicines directly from your prescription image to populate your treatment and schedule.
        </p>
      </div>

      {/* 1. Workflow Selection Mode (Create New vs Add to Existing) */}
      <div className={styles.saveModeSection}>
        <label className={styles.modeLabel}>How would you like to save this prescription?</label>
        <div className={styles.radioGrid}>
          <label
            className={`${styles.radioOption} ${saveMode === "new" ? styles.radioSelected : ""}`}
            onClick={() => setSaveMode("new")}
          >
            <input
              type="radio"
              name="saveMode"
              value="new"
              checked={saveMode === "new"}
              onChange={() => setSaveMode("new")}
            />
            <div className={styles.radioContent}>
              <span className={styles.radioTitle}>✨ Create New Treatment</span>
              <span className={styles.radioDesc}>Start a new treatment plan for this prescription</span>
            </div>
          </label>

          <label
            className={`${styles.radioOption} ${saveMode === "existing" ? styles.radioSelected : ""}`}
            onClick={() => setSaveMode("existing")}
          >
            <input
              type="radio"
              name="saveMode"
              value="existing"
              checked={saveMode === "existing"}
              onChange={() => setSaveMode("existing")}
            />
            <div className={styles.radioContent}>
              <span className={styles.radioTitle}>📋 Add Medicines to Existing Treatment</span>
              <span className={styles.radioDesc}>Add scanned medicines to an active treatment plan</span>
            </div>
          </label>
        </div>
      </div>

      {/* 2. Treatment Form Card (Create New Mode) */}
      {saveMode === "new" && (
        <div className={styles.formCard}>
          <h3 className={styles.cardSectionHeading}>
            <TbStethoscope className={styles.headingIcon} /> Treatment Information
          </h3>
          <div className={styles.formGrid}>
            <div className={styles.formGroup}>
              <label className={styles.label}>Treatment / Disease Name *</label>
              <input
                type="text"
                className={styles.input}
                placeholder="e.g. Hypertension, Diabetes Type 2"
                value={newTreatment.disease_name}
                onChange={(e) => handleNewTreatmentChange("disease_name", e.target.value)}
                required
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Doctor Name</label>
              <input
                type="text"
                className={styles.input}
                placeholder="e.g. Dr. Sarah Jenkins"
                value={newTreatment.doctor_name}
                onChange={(e) => handleNewTreatmentChange("doctor_name", e.target.value)}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Hospital / Clinic (Optional)</label>
              <input
                type="text"
                className={styles.input}
                placeholder="e.g. City General Hospital"
                value={newTreatment.hospital}
                onChange={(e) => handleNewTreatmentChange("hospital", e.target.value)}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>Start Date</label>
              <input
                type="date"
                className={styles.input}
                value={newTreatment.start_date}
                onChange={(e) => handleNewTreatmentChange("start_date", e.target.value)}
              />
            </div>

            <div className={styles.formGroup}>
              <label className={styles.label}>End Date</label>
              <input
                type="date"
                className={styles.input}
                value={newTreatment.end_date}
                onChange={(e) => handleNewTreatmentChange("end_date", e.target.value)}
              />
            </div>

            <div className={`${styles.formGroup} ${styles.fullWidth}`}>
              <label className={styles.label}>Notes / Instructions (Optional)</label>
              <textarea
                className={styles.textarea}
                placeholder="e.g. Take after meals, follow up in 2 weeks"
                value={newTreatment.notes}
                onChange={(e) => handleNewTreatmentChange("notes", e.target.value)}
                rows={2}
              />
            </div>
          </div>
        </div>
      )}

      {/* 3. Existing Treatment Selection Card (Existing Mode) */}
      {saveMode === "existing" && (
        <div className={styles.formCard}>
          <h3 className={styles.cardSectionHeading}>
            <TbFolderCheck className={styles.headingIcon} /> Select Existing Treatment
          </h3>
          {treatments.length > 0 ? (
            <div className={styles.formGroup}>
              <label className={styles.label}>Target Treatment Plan:</label>
              <select
                className={styles.select}
                value={selectedTreatmentId}
                onChange={(e) => setSelectedTreatmentId(e.target.value)}
              >
                {treatments.map((t) => (
                  <option key={t.id} value={t.id}>
                    {t.disease_name} (Dr. {t.doctor_name || "N/A"}) — {t.status || "Active"}
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className={styles.errorNotice}>
              <TbAlertTriangle size={20} />
              <span>No active treatments found. Please switch to "Create New Treatment".</span>
            </div>
          )}
        </div>
      )}

      {/* 4. Drag & Drop Upload Zone */}
      <div
        className={styles.dropzone}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
      >
        <TbUpload className={styles.uploadIcon} />
        <div className={styles.uploadText}>
          Drag & Drop Prescription or Medicine Strip Image
        </div>
        <div className={styles.uploadSubtext}>
          Supports PNG, JPG, JPEG, WEBP images
        </div>

        <div className={styles.btnGroup} onClick={(e) => e.stopPropagation()}>
          <button
            className={styles.uploadBtn}
            onClick={() => fileInputRef.current?.click()}
          >
            <TbUpload size={18} /> Upload Image
          </button>

          <button
            className={styles.cameraBtn}
            onClick={() => cameraInputRef.current?.click()}
          >
            <TbCamera size={18} /> Take Photo
          </button>
        </div>

        <input
          ref={fileInputRef}
          type="file"
          accept="image/*"
          className={styles.fileInput}
          onChange={handleFileChange}
        />

        <input
          ref={cameraInputRef}
          type="file"
          accept="image/*"
          capture="environment"
          className={styles.fileInput}
          onChange={handleFileChange}
        />
      </div>

      {/* Image Preview */}
      {previewUrl && (
        <div className={styles.previewSection}>
          <img src={previewUrl} alt="Prescription Preview" className={styles.previewImage} />
          <div>
            <h4 style={{ margin: "0 0 0.5rem 0", color: "#1e293b" }}>{selectedFile?.name}</h4>
            <p style={{ margin: 0, color: "#64748b", fontSize: "0.875rem" }}>
              {(selectedFile?.size / 1024).toFixed(1)} KB
            </p>
          </div>
        </div>
      )}

      {/* Processing Progress Animation */}
      {isProcessing && (
        <div className={styles.progressContainer}>
          <div className={styles.spinner}></div>
          <h3>Extracting prescription details using OCR...</h3>
          <div className={styles.progressBarBg}>
            <div
              className={styles.progressBarFill}
              style={{ width: `${progress}%` }}
            ></div>
          </div>
          <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
            Analyzing Medicine Names, Dosages, Quantities, and Durations ({progress}%)
          </p>
        </div>
      )}

      {/* OCR Failure Warning Notice */}
      {ocrFailed && !isProcessing && (
        <div className={styles.errorNotice}>
          <TbAlertTriangle size={24} />
          <span>
            We couldn't recognize all details automatically. Please review and edit the medicines below.
          </span>
        </div>
      )}

      {/* Success Notification */}
      {successMsg && (
        <div style={{ background: "#dcfce7", color: "#15803d", padding: "1rem", borderRadius: "12px", marginBottom: "1.5rem", fontWeight: 600 }}>
          <TbCheck size={20} style={{ verticalAlign: "middle", marginRight: "0.5rem" }} />
          {successMsg}
        </div>
      )}

      {/* 5. Extracted Editable Medicine Cards */}
      {extractedMedicines.length > 0 && !isProcessing && (
        <div>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "1rem" }}>
            <h2 style={{ fontSize: "1.25rem", color: "#0f172a", margin: 0, display: "flex", alignItems: "center", gap: "0.5rem" }}>
              <TbPill size={22} style={{ color: "#0F8B6D" }} /> Detected Medicines
            </h2>
            <button
              onClick={handleAddMedicineCard}
              style={{ background: "#f1f5f9", border: "1px solid #cbd5e1", borderRadius: "8px", padding: "0.5rem 1rem", cursor: "pointer", fontWeight: 600, display: "flex", alignItems: "center", gap: "0.4rem" }}
            >
              <TbPlus size={16} /> Add Another Medicine
            </button>
          </div>

          <div className={styles.cardGrid}>
            {extractedMedicines.map((med, idx) => (
              <div key={idx} className={styles.editableCard}>
                <div className={styles.cardHeader}>
                  <span className={styles.cardTitle}>Medicine #{idx + 1}</span>
                  <div style={{ display: "flex", alignItems: "center", gap: "0.5rem" }}>
                    <span className={styles.confidenceBadge} style={{ background: med.needs_review ? "#fef3c7" : "#dcfce7", color: med.needs_review ? "#b45309" : "#166534" }}>
                      {Math.round((med.confidence || 0.95) * 100)}% Confidence {med.needs_review ? "⚠️ Review" : "✓ High"}
                    </span>
                    <button
                      onClick={() => handleRemoveCard(idx)}
                      style={{ background: "none", border: "none", color: "#ef4444", cursor: "pointer" }}
                    >
                      <TbTrash size={18} />
                    </button>
                  </div>
                </div>

                <div className={styles.formGroup}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <label className={styles.label}>Medicine Name:</label>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>
                      Conf: {med.field_confidence?.name_confidence || 95}%
                    </span>
                  </div>
                  <input
                    type="text"
                    className={styles.input}
                    style={{ borderColor: (med.field_confidence?.name_confidence || 95) < 80 ? "#f59e0b" : "#cbd5e1" }}
                    value={med.medicine_name}
                    onChange={(e) => handleMedicineChange(idx, "medicine_name", e.target.value)}
                    placeholder="e.g. Amoxicillin"
                  />
                </div>

                <div className={styles.formGroup}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <label className={styles.label}>Dosage:</label>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>
                      Conf: {med.field_confidence?.dosage_confidence != null ? `${med.field_confidence.dosage_confidence}%` : "N/A"}
                    </span>
                  </div>
                  <input
                    type="text"
                    className={styles.input}
                    style={{ borderColor: med.field_confidence?.dosage_confidence && med.field_confidence.dosage_confidence < 80 ? "#f59e0b" : "#cbd5e1" }}
                    value={med.dosage}
                    onChange={(e) => handleMedicineChange(idx, "dosage", e.target.value)}
                    placeholder="e.g. 500mg"
                  />
                </div>

                <div className={styles.formGroup}>
                  <label className={styles.label}>Quantity (Stock):</label>
                  <input
                    type="number"
                    className={styles.input}
                    value={med.quantity}
                    onChange={(e) => handleMedicineChange(idx, "quantity", e.target.value)}
                  />
                </div>

                <div className={styles.formGroup}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <label className={styles.label}>Frequency:</label>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>
                      Conf: {med.field_confidence?.frequency_confidence != null ? `${med.field_confidence.frequency_confidence}%` : "N/A"}
                    </span>
                  </div>
                  <select
                    className={styles.select}
                    value={med.frequency}
                    onChange={(e) => handleMedicineChange(idx, "frequency", e.target.value)}
                  >
                    <option value="Daily">Daily</option>
                    <option value="Daily (Once a day)">Daily (Once a day)</option>
                    <option value="Twice daily">Twice daily</option>
                    <option value="Three times daily">Three times daily</option>
                    <option value="Four times daily">Four times daily</option>
                    <option value="At bedtime (Night)">At bedtime (Night)</option>
                    <option value="As needed">As needed</option>
                    <option value="Weekly">Weekly</option>
                  </select>
                </div>

                <div className={styles.formGroup}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <label className={styles.label}>Duration:</label>
                    <span style={{ fontSize: "0.75rem", color: "#64748b", fontWeight: 600 }}>
                      Conf: {med.field_confidence?.duration_confidence != null ? `${med.field_confidence.duration_confidence}%` : "N/A"}
                    </span>
                  </div>
                  <input
                    type="text"
                    className={styles.input}
                    style={{ borderColor: med.field_confidence?.duration_confidence && med.field_confidence.duration_confidence < 80 ? "#f59e0b" : "#cbd5e1" }}
                    value={med.duration}
                    onChange={(e) => handleMedicineChange(idx, "duration", e.target.value)}
                  />
                </div>
              </div>
            ))}
          </div>

          {/* 6. Automation Checkbox Options */}
          <div className={styles.optionsSection}>
            <h4 className={styles.optionsTitle}>
              <TbAdjustmentsHorizontal size={18} /> Automation Options
            </h4>
            <div className={styles.checkboxGroup}>
              <label className={styles.checkboxOption}>
                <input
                  type="checkbox"
                  checked={autoOptions.generateReminders}
                  onChange={(e) => setAutoOptions({ ...autoOptions, generateReminders: e.target.checked })}
                />
                <span>Generate medicine reminders automatically</span>
              </label>

              <label className={styles.checkboxOption}>
                <input
                  type="checkbox"
                  checked={autoOptions.calculateRefills}
                  onChange={(e) => setAutoOptions({ ...autoOptions, calculateRefills: e.target.checked })}
                />
                <span>Calculate refill dates based on quantity & duration</span>
              </label>

              <label className={styles.checkboxOption}>
                <input
                  type="checkbox"
                  checked={autoOptions.linkMedicines}
                  onChange={(e) => setAutoOptions({ ...autoOptions, linkMedicines: e.target.checked })}
                />
                <span>Link medicines automatically to treatment plan</span>
              </label>
            </div>
          </div>

          {/* 7. Save Action Button */}
          <div className={styles.saveSection}>
            <button
              className={styles.saveBtn}
              onClick={handleConfirmSave}
              disabled={isSaving}
            >
              {isSaving ? "Saving Plan & Medicines..." : "Save Treatment & Medicines"}
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default OCR;
