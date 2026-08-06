from enum import Enum


class HistoryStatus(str, Enum):
    TREATMENT_STARTED = "Treatment Started"
    TREATMENT_ACTIVE = "Treatment Active"
    COMPLETED = "Completed"
    MEDICINE_ADDED = "Medicine Added"
    MEDICINE_COMPLETED = "Medicine Completed"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"
    REMINDER_TRIGGERED = "Reminder Triggered"
    TAKEN = "Taken"
    SKIPPED = "Skipped"
    MISSED = "Missed"
    SNOOZED = "Snoozed"

