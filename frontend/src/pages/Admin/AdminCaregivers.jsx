import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbUserCheck } from "react-icons/tb";
import { getAdminCaregivers } from "../../services/adminService";

const AdminCaregivers = () => {
  const [caregivers, setCaregivers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchCaregivers = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminCaregivers();
        setCaregivers(data);
      } catch (err) {
        setError("Failed to load platform caregivers.");
      } finally {
        setLoading(false);
      }
    };

    fetchCaregivers();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Platform Caregivers Directory</h2>
          <p className="text-sm text-slate-500">View registered caregivers and their assigned patient caseloads.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading caregivers...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {caregivers.map((c) => (
              <div key={c.id} className="bg-white border border-slate-200 rounded-2xl p-5 shadow-xs space-y-3">
                <div className="flex items-start justify-between">
                  <div>
                    <h3 className="text-base font-bold text-slate-800">{c.full_name}</h3>
                    <p className="text-xs text-slate-500">{c.email}</p>
                  </div>
                  <span className="px-2.5 py-1 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200">
                    {c.assigned_count} Assigned Patients
                  </span>
                </div>

                <div className="border-t border-slate-100 pt-3">
                  <div className="text-xs font-bold text-slate-700 mb-2">Assigned Patients List:</div>
                  {c.assigned_patients.length === 0 ? (
                    <p className="text-xs text-slate-400 italic">No patients currently assigned.</p>
                  ) : (
                    <div className="flex flex-wrap gap-1.5">
                      {c.assigned_patients.map((p) => (
                        <span key={p.id} className="px-2 py-0.5 bg-slate-100 text-slate-700 rounded-lg text-xs font-medium">
                          {p.full_name}
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </PageContainer>
  );
};

export default AdminCaregivers;
