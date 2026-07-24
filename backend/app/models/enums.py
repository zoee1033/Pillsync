from enum import Enum


class HistoryStatus(str, Enum):
    COMPLETED = "Completed"
    MEDICINE_COMPLETED = "Medicine Completed"
    EXPIRED = "Expired"
    CANCELLED = "Cancelled"
    TAKEN = "Taken"
    SKIPPED = "Skipped"
    MISSED = "Missed"
    SNOOZED = "Snoozed"
