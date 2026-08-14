import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbUserHeart, TbUserPlus } from "react-icons/tb";
import { getAdminPatients, getAdminCaregivers, assignCaregiverToPatient } from "../../services/adminService";

const AdminPatients = () => {
  const [patients, setPatients] = useState([]);
  const [caregivers, setCaregivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [showModal, setShowModal] = useState(false);
  const [selectedPatientId, setSelectedPatientId] = useState(null);
  const [selectedCaregiverId, setSelectedCaregiverId] = useState("");
  const [assignLoading, setAssignLoading] = useState(false);

  const fetchData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [pRes, cRes] = await Promise.all([getAdminPatients(), getAdminCaregivers()]);
      setPatients(pRes);
      setCaregivers(cRes);
    } catch (err) {
      setError("Failed to load platform patients.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const handleAssignSubmit = async (e) => {
    e.preventDefault();
    if (!selectedPatientId || !selectedCaregiverId) return;

    setAssignLoading(true);
    try {
      await assignCaregiverToPatient(Number(selectedCaregiverId), Number(selectedPatientId));
      setShowModal(false);
      fetchData();
    } catch (err) {
      alert("Failed to assign caregiver: " + (err.response?.data?.detail || err.message));
    } finally {
      setAssignLoading(false);
    }
  };

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Platform Patients Directory</h2>
          <p className="text-sm text-slate-500">View and manage all registered patient profiles and caregiver assignments.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading patients...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Email</th>
                  <th className="py-3.5 px-4">Assigned Caregiver</th>
                  <th className="py-3.5 px-4">Active Meds</th>
                  <th className="py-3.5 px-4">Treatments</th>
                  <th className="py-3.5 px-4">Status</th>
                  <th className="py-3.5 px-4 text-right">Assign</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {patients.map((p) => (
                  <tr key={p.id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-slate-800">{p.full_name}</td>
                    <td className="py-3.5 px-4 text-slate-600">{p.email}</td>
                    <td className="py-3.5 px-4 font-semibold text-teal-700">{p.assigned_caregiver}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-800">{p.active_medicines}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-800">{p.active_treatments}</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        p.medication_status === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        p.medication_status === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                        'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {p.medication_status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <button
                        onClick={() => {
                          setSelectedPatientId(p.id);
                          setShowModal(true);
                        }}
                        className="text-xs font-bold text-[#0F8B6D] bg-[#0F8B6D]/10 hover:bg-[#0F8B6D]/20 px-3 py-1.5 rounded-xl border border-[#0F8B6D]/20 transition-colors"
                      >
                        Assign Caregiver
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>

      {/* Assign Caregiver Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-xl border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Assign Caregiver to Patient</h3>

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-semibold text-slate-700 mb-1">Select Caregiver</label>
                <select
                  required
                  value={selectedCaregiverId}
                  onChange={(e) => setSelectedCaregiverId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-300 rounded-xl text-sm focus:outline-none focus:border-[#0F8B6D]"
                >
                  <option value="">-- Choose Caregiver --</option>
                  {caregivers.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.full_name} ({c.email})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="px-4 py-2 text-xs font-semibold text-slate-600 bg-slate-100 rounded-xl"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={assignLoading}
                  className="px-4 py-2 text-xs font-semibold text-white bg-[#0F8B6D] rounded-xl"
                >
                  {assignLoading ? "Saving..." : "Confirm Assignment"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </PageContainer>
  );
};

export default AdminPatients;
