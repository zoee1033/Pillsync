export const HISTORY_STATUS = {
  COMPLETED: "Completed",
  MEDICINE_COMPLETED: "Medicine Completed",
  EXPIRED: "Expired",
  CANCELLED: "Cancelled",
  TAKEN: "Taken",
  SKIPPED: "Skipped",
  MISSED: "Missed",
  SNOOZED: "Snoozed",
};

export const STATUS_META = {
  [HISTORY_STATUS.COMPLETED]: {
    label: "Completed",
    icon: "✅",
    className: "statusCompleted",
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
