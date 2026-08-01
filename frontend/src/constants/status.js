export const HISTORY_STATUS = {
  TREATMENT_STARTED: "Treatment Started",
  TREATMENT_ACTIVE: "Treatment Active",
  COMPLETED: "Completed",
  MEDICINE_ADDED: "Medicine Added",
  MEDICINE_COMPLETED: "Medicine Completed",
  EXPIRED: "Expired",
  CANCELLED: "Cancelled",
  REMINDER_TRIGGERED: "Reminder Triggered",
  TAKEN: "Taken",
  SKIPPED: "Skipped",
  MISSED: "Missed",
  SNOOZED: "Snoozed",
};

export const STATUS_META = {
  [HISTORY_STATUS.TREATMENT_STARTED]: {
    label: "Treatment Started",
    icon: "🚀",
    className: "statusStarted",
  },
  [HISTORY_STATUS.TREATMENT_ACTIVE]: {
    label: "Treatment Active",
    icon: "🟢",
    className: "statusActive",
  },
  [HISTORY_STATUS.COMPLETED]: {
    label: "Completed",
    icon: "✅",
    className: "statusCompleted",
  },
  [HISTORY_STATUS.MEDICINE_ADDED]: {
    label: "Medicine Added",
    icon: "➕",
    className: "statusMedicineAdded",
  },
  [HISTORY_STATUS.MEDICINE_COMPLETED]: {
    label: "Medicine Completed",
    icon: "💊",
    className: "statusMedicineCompleted",
  },
  [HISTORY_STATUS.EXPIRED]: {
    label: "Expired",
    icon: "❌",
    className: "statusExpired",
  },
  [HISTORY_STATUS.CANCELLED]: {
    label: "Cancelled",
    icon: "🚫",
    className: "statusCancelled",
  },
  [HISTORY_STATUS.REMINDER_TRIGGERED]: {
    label: "Reminder Triggered",
    icon: "🔔",
    className: "statusReminderTriggered",
  },
  [HISTORY_STATUS.TAKEN]: {
    label: "Taken",
    icon: "✔",
    className: "statusTaken",
  },
  [HISTORY_STATUS.SKIPPED]: {
    label: "Skipped",
    icon: "⏭",
    className: "statusSkipped",
  },
  [HISTORY_STATUS.MISSED]: {
    label: "Missed",
    icon: "⚠️",
    className: "statusMissed",
  },
  [HISTORY_STATUS.SNOOZED]: {
    label: "Snoozed",
    icon: "😴",
    className: "statusSnoozed",
  },
};
