import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbPill, TbSearch } from "react-icons/tb";
import { getCaregiverMedicines } from "../../services/caregiverService";

const CaregiverMedicines = () => {
  const [medicines, setMedicines] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("All");

  useEffect(() => {
    const fetchMeds = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getCaregiverMedicines();
        setMedicines(data);
      } catch (err) {
        setError("Failed to load caregiver medicines overview.");
      } finally {
        setLoading(false);
      }
    };

    fetchMeds();
  }, []);

  const filteredMeds = medicines.filter((m) => {
    const matchesSearch =
      m.medicine_name.toLowerCase().includes(search.toLowerCase()) ||
      (m.patient_name && m.patient_name.toLowerCase().includes(search.toLowerCase()));

    if (statusFilter === "All") return matchesSearch;
    return matchesSearch && m.status_category === statusFilter;
  });

  return (
    <PageContainer>
      <div className="space-y-6">

        {/* Header */}
        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Caregiver Medicines Overview</h2>
          <p className="text-sm text-slate-500">View active medicines prescribed to all your assigned patients.</p>
        </div>

        {/* Filters */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 bg-white p-4 rounded-2xl border border-slate-200 shadow-xs">
          <div className="relative w-full sm:w-80">
            <TbSearch className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
            <input
              type="text"
              placeholder="Search medicine or patient name..."
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

        {/* Grid */}
        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading medicines...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : filteredMeds.length === 0 ? (
          <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <TbPill className="mx-auto text-slate-400 mb-2" size={44} />
            <h3 className="text-base font-semibold text-slate-700">No Medicines Found</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
              No active medicines match your search or filter for assigned patients.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {filteredMeds.map((m, idx) => (
              <div key={`${m.medicine_id}_${idx}`} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-800">{m.badge_icon || "💊"} {m.medicine_name}</h3>
                    <p className="text-xs text-slate-500">Patient: <strong className="text-slate-700">{m.patient_name}</strong></p>
                  </div>
                  <span className={`px-2.5 py-1 rounded-full text-xs font-bold ${
                    m.status_category === 'Healthy' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                    m.status_category === 'Needs Refill' ? 'bg-amber-50 text-amber-700 border border-amber-200' :
                    'bg-red-50 text-red-700 border border-red-200'
                  }`}>
                    {m.status_category} ({m.remaining_days} Days Left)
                  </span>
                </div>

                <div className="grid grid-cols-2 gap-2 text-xs border-t border-slate-100 pt-3 text-slate-600">
                  <div>Stock: <strong className="text-slate-800">{m.current_stock} Tablets</strong></div>
                  <div>Daily Usage: <strong className="text-slate-800">{m.daily_consumption}/day</strong></div>
                  <div className="col-span-2">Refill Recommended: <strong className="text-slate-800">{m.refill_date}</strong></div>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </PageContainer>
  );
};

export default CaregiverMedicines;
