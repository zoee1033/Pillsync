import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import PageContainer from "../../components/ui/PageContainer";
import ActionButton from "../../components/ui/ActionButton";
import { TbUsers, TbUserPlus, TbSearch, TbChevronRight } from "react-icons/tb";
import { getCaregiverPatients, linkPatientByEmail } from "../../services/caregiverService";

const CaregiverPatients = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  const [showLinkModal, setShowLinkModal] = useState(false);
  const [patientEmail, setPatientEmail] = useState("");
  const [linkLoading, setLinkLoading] = useState(false);
  const [linkMsg, setLinkMsg] = useState({ type: "", text: "" });

  const fetchPatients = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getCaregiverPatients();
      setPatients(data);
    } catch (err) {
      setError("Failed to load assigned patients.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPatients();
  }, []);

  const handleLinkSubmit = async (e) => {
    e.preventDefault();
    if (!patientEmail.trim()) return;

    setLinkLoading(true);
    setLinkMsg({ type: "", text: "" });
    try {
      const res = await linkPatientByEmail(patientEmail);
      setLinkMsg({ type: "success", text: res.message });
      setPatientEmail("");
      fetchPatients();
      setTimeout(() => setShowLinkModal(false), 1500);
    } catch (err) {
      setLinkMsg({ type: "error", text: err.response?.data?.detail || "Failed to link patient." });
    } finally {
      setLinkLoading(false);
    }
  };

  const filteredPatients = patients.filter((p) => {
    const matchesSearch =
      p.full_name.toLowerCase().includes(search.toLowerCase()) ||
      p.email.toLowerCase().includes(search.toLowerCase());

    if (statusFilter === "All") return matchesSearch;
    return matchesSearch && p.medication_status === statusFilter;
  });

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-2xl font-bold tracking-tight text-slate-800">My Patients</h2>
            <p className="text-sm text-slate-500">Monitor and manage medication health for your assigned patients.</p>
          </div>
          <ActionButton variant="primary" onClick={() => setShowLinkModal(true)}>
            <TbUserPlus className="inline mr-1.5" /> Link Patient
          </ActionButton>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="relative w-full sm:w-80">
            <TbSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search patients by name or email..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-[#0F8B6D]"
            />
          </div>

          <div className="flex items-center gap-2 overflow-x-auto w-full sm:w-auto">
            {["All", "Healthy", "Needs Refill", "Critical"].map((st) => (
              <button
                key={st}
                onClick={() => setStatusFilter(st)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-colors ${
                  statusFilter === st
                    ? "bg-[#0F8B6D] text-white"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {st}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading patients list...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : filteredPatients.length === 0 ? (
          <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <TbUsers className="mx-auto text-slate-400 mb-2" size={44} />
            <h3 className="text-base font-semibold text-slate-700">No Patients Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              {search || statusFilter !== "All"
                ? "No patients match your search or filter criteria."
                : "No patients are currently assigned to you. Click 'Link Patient' to add a patient by email."}
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredPatients.map((p) => (
              <div key={p.patient_id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs hover:border-[#0F8B6D]/40 transition-all flex flex-col justify-between">
                <div>
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="text-base font-bold text-slate-800">{p.full_name}</h3>
                      <p className="text-xs text-slate-500">{p.email}</p>
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                      p.medication_status === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                      p.medication_status === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                      'bg-red-50 text-red-700 border border-red-200'
                    }`}>
                      {p.medication_status}
                    </span>
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-2 text-xs border-t border-b border-slate-100 py-3">
                    <div>Active Meds: <strong className="text-slate-800">{p.active_medicine_count}</strong></div>
                    <div>Today's Adherence: <strong className="text-slate-800">{p.today_progress_pct}%</strong></div>
                    <div>Completed: <strong className="text-slate-800">{p.today_completed}</strong></div>
                    <div>Missed: <strong className="text-slate-800">{p.today_missed}</strong></div>
                  </div>

                  <div className="mt-3 text-xs text-slate-500 truncate">
                    Next Reminder: <strong className="text-slate-700">{p.next_reminder}</strong>
                  </div>
                </div>

                <div className="mt-5 flex justify-end">
                  <Link
                    to={`/caregiver/patients/${p.patient_id}`}
                    className="text-xs font-bold text-white bg-[#0F8B6D] hover:bg-[#0D7A60] px-4 py-2 rounded-xl flex items-center gap-1 transition-colors"
                  >
                    View Patient <TbChevronRight size={14} />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>

      {/* Link Patient Modal */}
      {showLinkModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-1">Link New Patient</h3>
            <p className="text-xs text-slate-500 mb-4">Enter the registered email address of the patient you want to monitor.</p>

            {linkMsg.text && (
              <div className={`p-3 text-xs rounded-xl mb-3 ${linkMsg.type === 'success' ? 'bg-emerald-50 text-emerald-800 border border-emerald-200' : 'bg-red-50 text-red-800 border border-red-200'}`}>
                {linkMsg.text}
              </div>
            )}

            <form onSubmit={handleLinkSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Patient Email Address</label>
                <input
                  type="email"
                  required
                  placeholder="e.g. patient@gmail.com"
                  value={patientEmail}
                  onChange={(e) => setPatientEmail(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:border-[#0F8B6D]"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowLinkModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 hover:bg-slate-200 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={linkLoading}
                  className="px-4 py-2 text-xs font-semibold text-white bg-[#0F8B6D] hover:bg-[#0D7A60] rounded-xl"
                >
                  {linkLoading ? "Assigning..." : "Assign Patient"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
};

export default CaregiverPatients;
