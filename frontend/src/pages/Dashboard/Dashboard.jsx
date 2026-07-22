import React, { useMemo } from "react";
// Using CSS-based transitions instead of framer-motion to avoid peer dependency issues
import useAuth from "../../hooks/useAuth";
import PageHeader from "../../components/ui/PageHeader";
import SearchBar from "../../components/ui/SearchBar";
import SummaryCard from "../../components/ui/SummaryCard";
import StatsCard from "../../components/ui/StatsCard";
import StatusBadge from "../../components/ui/StatusBadge";
import EmptyState from "../../components/ui/EmptyState";
import LoadingSkeleton from "../../components/ui/LoadingSkeleton";
import ActionButton from "../../components/ui/ActionButton";
import PageContainer from "../../components/ui/PageContainer";
import CardContainer from "../../components/ui/CardContainer";
import { TbPill, TbClock, TbPlus, TbList, TbActivity } from "react-icons/tb";
import { Link } from "react-router-dom";

const DashboardContent = () => {
  const { user } = useAuth();

  const currentUser = user || { full_name: "Health User", role: "patient" };

  const currentDate = useMemo(
    () =>
      new Date().toLocaleDateString("en-US", {
        weekday: "long",
        year: "numeric",
        month: "long",
        day: "numeric",
      }),
    []
  );

  // Dummy data (no hardcoded styling; data only)
  const summaries = [
    { title: "Today's Medicines", value: 6, hint: '3 completed, 3 remaining', icon: <TbPill className="text-primary" /> },
    { title: 'Upcoming Reminder', value: '14:30', hint: 'Vitamin D 1000 IU', icon: <TbClock className="text-primary" /> },
    { title: 'Medicines Taken', value: '4', hint: 'This Week', icon: <TbList className="text-primary" /> },
  ];

  const schedule = [
    { time: '08:00 AM', medicine: 'Metformin 500mg', status: 'Pending' },
    { time: '02:00 PM', medicine: 'Vitamin D 1000 IU', status: 'Taken' },
    { time: '08:00 PM', medicine: 'Insulin', status: 'Upcoming' },
  ];

  const recent = [
    { id: 1, text: 'Metformin taken', time: '08:05 AM' },
    { id: 2, text: 'Reminder snoozed', time: '09:12 AM' },
  ];

  return (
    <PageContainer>
      <div className="transition-all duration-300 ease-out">
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-semibold text-text-primary">Good Morning, {currentUser.full_name.split(' ')[0] || 'User'} 👋</h1>
            <p className="text-sm text-text-secondary">{currentDate}</p>
          </div>

          <div className="w-80">
            <SearchBar placeholder="Search medicines, reminders..." />
          </div>
        </div>

        {/* Summary Cards */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 mb-6">
          {summaries.map((s) => (
            <SummaryCard key={s.title} title={s.title} value={s.value} hint={s.hint} icon={s.icon} />
          ))}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Today's Schedule + Quick Actions */}
          <div className="space-y-6 lg:col-span-2">
            <StatsCard title="Today's Schedule" series={
              <div className="space-y-3">
                {schedule.map((item) => (
                  <div key={item.time} className="flex items-center justify-between bg-card border border-border rounded-xl p-3">
                    <div>
                      <div className="text-sm text-text-secondary">{item.time}</div>
                      <div className="font-medium text-text-primary">{item.medicine}</div>
                    </div>
                    <div>
                      <StatusBadge status={item.status} />
                    </div>
                  </div>
                ))}
              </div>
            } footer={<></>} />

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <StatsCard title="Medicine Adherence" series={<div className="h-36 flex items-center justify-center"> <div className="text-3xl font-bold">92%</div></div>} footer={<div className="text-sm text-text-secondary">This Week</div>} />

              <StatsCard title="Next Reminder" series={<div className="p-4"> <div className="text-lg font-semibold">Vitamin D 1000 IU</div> <div className="text-sm text-text-secondary">1 tablet after lunch</div> </div>} footer={<ActionButton as={Link} to="#" variant="outline">Snooze 10m</ActionButton>} />
            </div>

            <div>
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-lg font-semibold text-text-primary">Recent Activity</h3>
                <ActionButton variant="outline">View All</ActionButton>
              </div>

              <div className="space-y-3">
                {recent.map((r) => (
                  <div key={r.id} className="flex items-center justify-between bg-card border border-border rounded-xl p-3">
                    <div className="flex items-center gap-3">
                      <div className="p-2 bg-primary/10 rounded-md"><TbActivity /></div>
                      <div>
                        <div className="text-sm text-text-primary">{r.text}</div>
                        <div className="text-xs text-text-secondary">{r.time}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Right Column: Quick Actions / Overview */}
          <aside className="space-y-6">
            <div className="bg-card border border-border rounded-xl p-4">
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-sm text-text-secondary">Quick Actions</h4>
                <StatusBadge status="Active" />
              </div>
              <div className="grid grid-cols-1 gap-3">
                <ActionButton as={Link} to="#" variant="primary"><TbPlus className="inline mr-2"/> Add Reminder</ActionButton>
                <ActionButton as={Link} to="#" variant="outline"><TbPlus className="inline mr-2"/> Add Medicine</ActionButton>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-4">
              <h4 className="text-sm text-text-secondary mb-2">Medicine Adherence</h4>
              <div className="text-center">
                <div className="text-2xl font-bold">92%</div>
                <div className="text-xs text-text-secondary">Taken</div>
              </div>
            </div>

            <div className="bg-card border border-border rounded-xl p-4">
              <h4 className="text-sm text-text-secondary mb-2">Empty State Example</h4>
              <EmptyState title="No low stock alerts" message="All medicines are sufficiently stocked." />
            </div>
          </aside>
        </div>
      </div>
    </PageContainer>
  );
};

const Dashboard = () => {
  return <DashboardContent />;
};

export default Dashboard;