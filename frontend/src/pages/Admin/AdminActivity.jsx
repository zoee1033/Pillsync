import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbActivity } from "react-icons/tb";
import { getAdminActivity } from "../../services/adminService";

const AdminActivity = () => {
  const [activities, setActivities] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchActivities = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminActivity();
        setActivities(data);
      } catch (err) {
        setError("Failed to load platform activity feed.");
      } finally {
        setLoading(false);
      }
    };

    fetchActivities();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Platform Activity Audit Log</h2>
          <p className="text-sm text-slate-500">Real-time audit log of user dose events, stock updates, and system activity.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading activity feed...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : activities.length === 0 ? (
          <div className="text-center py-12 px-4 bg-slate-50 rounded-2xl border border-dashed border-slate-200">
            <TbActivity className="mx-auto text-slate-400 mb-2" size={44} />
            <h3 className="text-base font-semibold text-slate-700">No Activity Logged</h3>
            <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">No recent system activity events found.</p>
          </div>
        ) : (
          <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-xs">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                  <th className="py-3.5 px-4">Timestamp</th>
                  <th className="py-3.5 px-4">User</th>
                  <th className="py-3.5 px-4">Action</th>
                  <th className="py-3.5 px-4">Target</th>
                  <th className="py-3.5 px-4">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {activities.map((act) => (
                  <tr key={act.id} className="hover:bg-slate-50/50">
                    <td className="py-3.5 px-4 text-xs font-medium text-slate-500">{act.timestamp}</td>
                    <td className="py-3.5 px-4 font-bold text-slate-800">{act.user_name}</td>
                    <td className="py-3.5 px-4 font-medium text-slate-700">{act.action}</td>
                    <td className="py-3.5 px-4 text-xs text-slate-600">{act.target}</td>
                    <td className="py-3.5 px-4">
                      <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-slate-100 text-slate-800">
                        {act.status}
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

export default AdminActivity;
