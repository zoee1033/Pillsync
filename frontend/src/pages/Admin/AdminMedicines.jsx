import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbPill, TbSearch } from "react-icons/tb";
import { getAdminMedicines } from "../../services/adminService";

const AdminMedicines = () => {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");

  useEffect(() => {
    const fetchMeds = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminMedicines();
        setMedicines(data);
      } catch (err) {
        setError("Failed to load platform medicines.");
      } finally {
        setLoading(false);
      }
    };

    fetchMeds();
  }, []);

  const filteredMeds = medicines.filter((m) =>
    m.medicine_name.toLowerCase().includes(search.toLowerCase()) ||
    (m.patient_name && m.patient_name.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">System Active Medicines</h2>
          <p className="text-sm text-slate-500">Overview of all active prescribed medicines across the PillSync platform.</p>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-xs max-w-md">
          <div className="relative">
            <TbSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search medicine or patient..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="w-full pl-10 pr-4 py-2 text-sm border border-slate-200 rounded-xl focus:outline-none focus:border-purple-600"
            />
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading platform medicines...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Medicine Name</th>
                  <th className="py-3.5 px-4">Patient</th>
                  <th className="py-3.5 px-4">Stock</th>
                  <th className="py-3.5 px-4">Daily Usage</th>
                  <th className="py-3.5 px-4">Days Remaining</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {filteredMeds.map((m, idx) => (
                  <tr key={`${m.medicine_id}_${idx}`} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 font-bold text-slate-800">{m.badge_icon || "💊"} {m.medicine_name}</td>
                    <td className="py-3.5 px-4 font-semibold text-slate-700">{m.patient_name}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-800">{m.current_stock} Tablets</td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{m.daily_consumption}/day</td>
                    <td className="py-3.5 px-4 text-xs font-bold text-slate-700">{m.remaining_days} Days</td>
                    <td className="py-3.5 px-4">
                      <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                        m.status_category === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                        m.status_category === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                        'bg-red-50 text-red-700 border border-red-200'
                      }`}>
                        {m.status_category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </PageContainer>
  );
};

export default AdminMedicines;
