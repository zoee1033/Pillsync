import React, { useState, useEffect } from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbBell } from "react-icons/tb";
import { getAdminNotifications } from "../../services/adminService";

const AdminNotifications = () => {
  const [notifications, setNotifications] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchNotifs = async () => {
      setLoading(true);
      setError(null);
      try {
        const data = await getAdminNotifications();
        setNotifications(data);
      } catch (err) {
        setError("Failed to load platform notifications.");
      } finally {
        setLoading(false);
      }
    };

    fetchNotifs();
  }, []);

  return (
    <PageContainer>
      <div className="space-y-6">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">System Notifications Feed</h2>
          <p className="text-sm text-slate-500">System-wide notifications dispatched across all platform users.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500 font-medium">Loading notifications...</div>
        ) : error ? (
          <div className="p-4 bg-red-50 text-red-700 rounded-xl border border-red-200">{error}</div>
        ) : (
          <div className="space-y-3 max-w-3xl">
            {notifications.map((n) => (
              <div key={n.id} className="p-4 bg-white border border-slate-200 rounded-2xl shadow-xs flex items-start gap-3">
                <div className="p-2 bg-purple-100 text-purple-700 rounded-xl mt-0.5">
                  <TbBell size={20} />
                </div>
                <div className="flex-1">
                  <div className="flex items-center justify-between">
                    <h4 className="text-sm font-bold text-slate-800">{n.user_name}: {n.title}</h4>
                    <span className="text-[11px] text-slate-400">{n.created_at ? new Date(n.created_at).toLocaleString() : ''}</span>
                  </div>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{n.message}</p>
                </div>
              </div>
            ))}
          </div>
        )}

      </div>
    </PageContainer>
  );
};

export default AdminNotifications;
