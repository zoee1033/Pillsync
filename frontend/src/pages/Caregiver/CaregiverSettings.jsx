import React from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbSettings, TbBell, TbShieldLock } from "react-icons/tb";

const CaregiverSettings = () => {
  return (
    <PageContainer>
      <div className="space-y-6 max-w-2xl">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Caregiver Settings</h2>
          <p className="text-sm text-slate-500">Configure caregiver workspace preferences and notifications.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
          
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <TbBell className="text-[#0F8B6D]" size={20} /> Patient Monitoring Notifications
            </h3>

            <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl cursor-pointer">
              <span className="text-sm font-medium text-slate-700">Receive alert when assigned patient misses a dose</span>
              <input type="checkbox" defaultChecked className="w-4 h-4 accent-[#0F8B6D]" />
            </label>

            <label className="flex items-center justify-between p-3 bg-slate-50 rounded-xl cursor-pointer">
              <span className="text-sm font-medium text-slate-700">Receive alert when assigned patient medicine stock is critical</span>
              <input type="checkbox" defaultChecked className="w-4 h-4 accent-[#0F8B6D]" />
            </label>
          </div>

          <div className="space-y-3 border-t border-slate-100 pt-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <TbShieldLock className="text-[#0F8B6D]" size={20} /> Role Authorization
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Your account is authenticated as a <strong>Caregiver</strong>. You are authorized to view and monitor medication health metrics only for patients explicitly assigned to you.
            </p>
          </div>

        </div>

      </div>
    </PageContainer>
  );
};

export default CaregiverSettings;
