import React from "react";
import PageContainer from "../../components/ui/PageContainer";
import { TbUserCheck, TbMail, TbPhone, TbId } from "react-icons/tb";
import useAuth from "../../hooks/useAuth";

const CaregiverProfile = () => {
  const { user } = useAuth();

  return (
    <PageContainer>
      <div className="space-y-6 max-w-2xl">

        <div>
          <h2 className="text-2xl font-bold tracking-tight text-slate-800">Caregiver Profile</h2>
          <p className="text-sm text-slate-500">Your authenticated caregiver account details.</p>
        </div>

        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-xs space-y-4">
          <div className="flex items-center gap-4 border-b border-slate-100 pb-4">
            <div className="w-16 h-16 rounded-full bg-teal-100 text-teal-800 flex items-center justify-center font-bold text-2xl">
              {user?.full_name ? user.full_name.charAt(0).toUpperCase() : "C"}
            </div>
            <div>
              <h3 className="text-lg font-bold text-slate-800">{user?.full_name || "Caregiver Account"}</h3>
              <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-teal-50 text-teal-700 border border-teal-200">
                Caregiver Role
              </span>
            </div>
          </div>

          <div className="space-y-3 text-sm">
            <div className="flex items-center gap-3">
              <TbMail className="text-slate-400" size={18} />
              <div>
                <div className="text-xs text-slate-500 font-medium">Email Address</div>
                <div className="font-semibold text-slate-800">{user?.email || "—"}</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <TbPhone className="text-slate-400" size={18} />
              <div>
                <div className="text-xs text-slate-500 font-medium">Phone Number</div>
                <div className="font-semibold text-slate-800">{user?.phone || "Not provided"}</div>
              </div>
            </div>

            <div className="flex items-center gap-3">
              <TbId className="text-slate-400" size={18} />
              <div>
                <div className="text-xs text-slate-500 font-medium">User Account ID</div>
                <div className="font-semibold text-slate-800">#{user?.id}</div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </PageContainer>
  );
};

export default CaregiverProfile;
