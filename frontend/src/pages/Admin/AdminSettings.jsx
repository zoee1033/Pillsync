import React from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbShieldCheck, TbServer, TbLock } from "react-icons/tb";

const AdminSettings = () => {
  return (
    <PageContainer>
      <div className="space-y-6 max-w-2xl">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Admin System Settings</h2>
          <p className="text-sm text-slate-500">Platform security and system-wide configuration controls.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-6">
          
          <div className="space-y-3">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <TbShieldCheck className="text-purple-600" size={20} /> Role-Based Access Control (RBAC)
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              RBAC enforcement is active. Patients, Caregivers, and Admins are restricted to authorized frontend routes and backend APIs.
            </p>
          </div>

          <div className="space-y-3 border-t border-slate-100 pt-4">
            <h3 className="text-base font-bold text-slate-800 flex items-center gap-2">
              <TbServer className="text-purple-600" size={20} /> Platform Security Policy
            </h3>
            <p className="text-xs text-slate-500 leading-relaxed">
              Sensitive authentication details (passwords, JWT secrets, database connection strings, SMTP credentials, Firebase keys) are strictly hidden from administrative user management interfaces.
            </p>
          </div>

        </div>

      </div>
    </PageContainer>
  );
};

export default AdminSettings;
