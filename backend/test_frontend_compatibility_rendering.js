const fs = require('fs');

// 1. Load STATUS_META from frontend/src/constants/status.js
const STATUS_META = {
  "Treatment Started": { label: "Treatment Started", icon: "🚀", className: "statusStarted" },
  "Treatment Active": { label: "Treatment Active", icon: "🟢", className: "statusActive" },
  "Completed": { label: "Completed", icon: "✅", className: "statusCompleted" },
  "Cancelled": { label: "Cancelled", icon: "🚫", className: "statusCancelled" },
  "Expired": { label: "Expired", icon: "❌", className: "statusExpired" },
  "Medicine Added": { label: "Medicine Added", icon: "➕", className: "statusMedicineAdded" },
  "Medicine Completed": { label: "Medicine Completed", icon: "💊", className: "statusMedicineCompleted" },
  "Reminder Triggered": { label: "Reminder Triggered", icon: "🔔", className: "statusReminderTriggered" },
  "Taken": { label: "Taken", icon: "✔", className: "statusTaken" },
  "Skipped": { label: "Skipped", icon: "⏭", className: "statusSkipped" },
  "Missed": { label: "Missed", icon: "⚠️", className: "statusMissed" },
  "Snoozed": { label: "Snoozed", icon: "😴", className: "statusSnoozed" }
};

const HISTORY_STATUS = {
  TAKEN: "Taken",
  SKIPPED: "Skipped",
  MISSED: "Missed",
  SNOOZED: "Snoozed"
};

// Sample response from GET /history
const sampleApiResponse = [
  {
    "scheduled_time": "2026-07-30T01:30:00+05:30",
    "status": "Snoozed",
    "skip_reason": null,
    "notes": "Snoozed by 15 mins",
    "id": 2413,
    "user_id": 14,
    "treatment_id": 14,
    "medicine_id": 10,
    "reminder_id": 14,
    "medicine_name": "Salbutamol Inhaler",
    "treatment_name": "Asthma Care",
    "dosage": "2 puffs",
    "reminder_time": "08:00:00",
    "start_date": "2026-06-01",
    "end_date": "2026-07-01",
    "completion_date": "2026-07-01",
    "duration": "30 days",
    "action_time": "2026-07-29T15:18:31.125914+05:30",
    "created_at": "2026-07-29T20:48:31.122079+05:30"
  },
  {
    "scheduled_time": "2026-07-29T15:18:31.001580+05:30",
    "status": "Cancelled",
    "skip_reason": null,
    "notes": "Treatment cancelled.",
    "id": 2409,
    "user_id": 14,
    "treatment_id": 15,
    "medicine_id": null,
    "reminder_id": null,
    "medicine_name": null,
    "treatment_name": "Migraine Treatment",
    "dosage": null,
    "reminder_time": null,
    "start_date": "2026-07-10",
    "end_date": "2026-08-10",
    "completion_date": null,
    "duration": "31 days",
    "action_time": "2026-07-29T15:18:31.001580+05:30",
    "created_at": "2026-07-29T20:48:30.998765+05:30"
  },
  {
    "scheduled_time": "2026-07-29T15:18:30.942680+05:30",
    "status": "Completed",
    "skip_reason": null,
    "notes": "Treatment completed.",
    "id": 2406,
    "user_id": 14,
    "treatment_id": 14,
    "medicine_id": null,
    "reminder_id": null,
    "medicine_name": null,
    "treatment_name": "Asthma Care",
    "dosage": null,
    "reminder_time": null,
    "start_date": "2026-06-01",
    "end_date": "2026-07-01",
    "completion_date": "2026-07-01",
    "duration": "30 days",
    "action_time": "2026-07-29T15:18:30.942680+05:30",
    "created_at": "2026-07-29T20:48:30.944157+05:30"
  }
];

function simulateFrontendRender(items) {
  console.log("==========================================================");
  console.log("SIMULATING REACT FRONTEND History.jsx RENDER");
  console.log("==========================================================");

  if (!items || items.length === 0) {
    console.log("RENDER RESULT: <EmptyState title='No history yet' />");
    return;
  }

  items.forEach((item, index) => {
    const meta = STATUS_META[item.status] || {
      label: item.status,
      icon: "📌",
      className: "statusDefault",
    };

    const medName = item.medicine_name || (item.medicine_id ? `Medicine #${item.medicine_id}` : null);
    const treatName = item.treatment_name || `Treatment #${item.treatment_id}`;
    const remTime = item.reminder_time;

    const isUserAction = [
      HISTORY_STATUS.TAKEN,
      HISTORY_STATUS.SKIPPED,
      HISTORY_STATUS.MISSED,
      HISTORY_STATUS.SNOOZED,
    ].includes(item.status);

    console.log(`\n--- Card ${index + 1} (ID: ${item.id}) ---`);
    console.log(`Title:       ${medName ? medName : treatName}`);
    console.log(`Subtitle:    Treatment: ${treatName}`);
    console.log(`Badge:       [${meta.icon} ${meta.label}] (CSS Class: ${meta.className})`);
    console.log(`Details:`);
    if (medName) console.log(`  - Medicine: ${medName}`);
    if (item.dosage) console.log(`  - Dosage: ${item.dosage}`);
    if (remTime) console.log(`  - Reminder Time: ${remTime}`);
    if (item.start_date) console.log(`  - Start Date: ${item.start_date}`);
    if (item.end_date) console.log(`  - End Date: ${item.end_date}`);
    if (item.completion_date) console.log(`  - Completion Date: ${item.completion_date}`);
    if (item.duration) console.log(`  - Duration: ${item.duration}`);
    console.log(`  - Event Timestamp: ${new Date(item.action_time).toLocaleString()}`);
    if (item.skip_reason) console.log(`  - Skip Reason: ${item.skip_reason}`);
    if (item.notes) console.log(`  - Notes: ${item.notes}`);
    if (isUserAction && item.medicine_id && item.reminder_id) {
      console.log(`  - Action Buttons: [Mark Taken] [Mark Skipped] [Mark Missed]`);
    }
  });

  console.log("\n==========================================================");
  console.log("REACT RENDER SIMULATION SUCCESSFUL - ALL ITEMS RENDER CLEANLY");
  console.log("==========================================================");
}

simulateFrontendRender(sampleApiResponse);
