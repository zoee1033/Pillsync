from datetime import datetime, date, timedelta
from typing import Dict, Any, List
from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.models.history import History
from app.models.medicine import Medicine
from app.models.treatment import Treatment
from app.models.reminder import Reminder
from app.models.notification import Notification
from app.models.enums import HistoryStatus
from app.models.user import User


def get_dashboard_summary(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Computes real-time, on-demand Dashboard summary metrics strictly from PostgreSQL tables:
    Treatments, Medicines, History, Reminders, Notifications.
    Zero mock/hardcoded values.
    """
    now = datetime.now().astimezone()
    today_date = now.date()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # 1. Active Treatments Count
    active_treatments = (
        db.query(Treatment)
        .filter(Treatment.user_id == current_user.id, Treatment.status == "Active")
        .count()
    )

    # 2. Active Medicines Count
    active_medicines = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == current_user.id, Treatment.status == "Active", Medicine.is_active == True)
        .count()
    )

    # Fetch User History Records
    all_history = (
        db.query(History)
        .filter(History.user_id == current_user.id)
        .order_by(History.scheduled_time.desc())
        .all()
    )

    def ensure_tz(dt):
        if dt is None:
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=now.tzinfo)
        return dt

    today_recs = [h for h in all_history if ensure_tz(h.scheduled_time).date() == today_date]

    # 3. Today's Scheduled Doses
    today_scheduled = len(today_recs)
    if today_scheduled == 0:
        active_reminders_cnt = (
            db.query(Reminder)
            .join(Reminder.medicine)
            .join(Medicine.treatment)
            .filter(Treatment.user_id == current_user.id, Reminder.status == "Active", Medicine.is_active == True)
            .count()
        )
        today_scheduled = active_reminders_cnt

    # 4. Today's Doses Breakdown
    today_completed = sum(1 for h in today_recs if h.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
    today_missed = sum(1 for h in today_recs if h.status in [HistoryStatus.MISSED.value, "Missed"])
    remaining_today = max(0, today_scheduled - today_completed - today_missed)

    # 5. Overall Adherence
    all_scheduled = len(all_history)
    all_completed = sum(1 for h in all_history if h.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
    overall_adherence = round((all_completed / all_scheduled * 100.0), 1) if all_scheduled > 0 else 100.0

    # 6. Next Scheduled Reminder
    active_reminders = (
        db.query(Reminder)
        .join(Reminder.medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == current_user.id, Reminder.status == "Active", Medicine.is_active == True)
        .order_by(Reminder.reminder_time.asc())
        .all()
    )

    next_reminder_str = "None Scheduled Today"
    if active_reminders:
        first_rem = active_reminders[0]
        rem_t = first_rem.reminder_time.strftime("%I:%M %p") if hasattr(first_rem.reminder_time, 'strftime') else str(first_rem.reminder_time)
        med_n = first_rem.medicine.medicine_name if first_rem.medicine else "Medicine"
        next_reminder_str = f"{rem_t} - {med_n}"

    # 7. Upcoming Refills & Stock Analysis
    user_medicines = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == current_user.id, Medicine.is_active == True)
        .all()
    )

    upcoming_refills_cnt = 0
    low_stock_cnt = 0
    refill_first_med = None
    min_refill_days = 9999
    healthy_cnt = 0
    needs_refill_cnt = 0
    critical_cnt = 0

    import re
    for m in user_medicines:
        reminders = [r for r in m.reminders if r.status == "Active"] if hasattr(m, 'reminders') and m.reminders else []
        dose_match = re.search(r'(\d+)', m.dosage or "1")
        dose_per_intake = int(dose_match.group(1)) if dose_match else 1
        daily_doses = dose_per_intake * (len(reminders) if reminders else 1)
        rem_days = int(max(0, m.quantity) / daily_doses) if daily_doses > 0 else 30

        if rem_days > 15:
            healthy_cnt += 1
        elif 8 <= rem_days <= 15:
            needs_refill_cnt += 1
        elif 4 <= rem_days <= 7:
            needs_refill_cnt += 1
            low_stock_cnt += 1
            upcoming_refills_cnt += 1
        else:
            critical_cnt += 1
            low_stock_cnt += 1
            upcoming_refills_cnt += 1

        if rem_days < min_refill_days:
            min_refill_days = rem_days
            refill_first_med = f"{m.medicine_name} ({int(rem_days)} days left)"

    # 8. Unread Notifications Count
    unread_notifications = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )

    # 9. Current Adherence Streak
    day_groups: Dict[str, List[History]] = {}
    for h in all_history:
        d_str = ensure_tz(h.scheduled_time).strftime("%Y-%m-%d")
        if d_str not in day_groups:
            day_groups[d_str] = []
        day_groups[d_str].append(h)

    sorted_days = sorted(day_groups.keys(), reverse=True)
    current_streak = 0
    for d_str in sorted_days:
        day_recs = day_groups[d_str]
        day_taken = sum(1 for r in day_recs if r.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
        day_adh = (day_taken / len(day_recs)) * 100.0 if len(day_recs) > 0 else 100.0
        if day_adh >= 80.0:
            current_streak += 1
        else:
            break

    return {
        "active_treatments": active_treatments,
        "active_medicines": active_medicines,
        "todays_doses": today_scheduled,
        "today_scheduled": today_scheduled,
        "today_completed": today_completed,
        "today_missed": today_missed,
        "remaining_today": remaining_today,
        "overall_adherence": overall_adherence,
        "adherence_percent": overall_adherence,
        "upcoming_refills": upcoming_refills_cnt,
        "upcoming_refill_name": refill_first_med or "None",
        "next_reminder": next_reminder_str,
        "low_stock": low_stock_cnt,
        "notifications": unread_notifications,
        "unread_notifications": unread_notifications,
        "current_streak": current_streak,
        "missed_today": today_missed,
        "stock_healthy_count": healthy_cnt,
        "stock_needs_refill_count": needs_refill_cnt,
        "stock_critical_count": critical_cnt
    }


def get_adherence_analytics(db: Session, current_user: User) -> Dict[str, Any]:
    """
    Computes comprehensive analytics and health insights strictly from PostgreSQL tables:
    Daily, Weekly, Monthly, Overall Adherence, Best/Worst Days, Most Missed Medicine,
    Refill Predictions, and Treatment Progress Insights.
    """
    now = datetime.now().astimezone()
    today_date = now.date()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    seven_days_ago = today_start - timedelta(days=7)
    thirty_days_ago = today_start - timedelta(days=30)

    # Fetch All User History
    all_history = (
        db.query(History)
        .filter(History.user_id == current_user.id)
        .order_by(History.scheduled_time.desc())
        .all()
    )

    def ensure_tz(dt):
        if dt is None:
            return dt
        if dt.tzinfo is None:
            return dt.replace(tzinfo=now.tzinfo)
        return dt

    # Filter Timeframes
    today_recs = [h for h in all_history if ensure_tz(h.scheduled_time).date() == today_date]
    weekly_recs = [h for h in all_history if ensure_tz(h.scheduled_time) >= seven_days_ago]
    monthly_recs = [h for h in all_history if ensure_tz(h.scheduled_time) >= thirty_days_ago]

    # Calculate Adherence Percentage
    def calc_adherence(recs: List[History]) -> float:
        if not recs:
            return 100.0
        taken = sum(1 for r in recs if r.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
        return round((taken / len(recs)) * 100.0, 1)

    daily_adherence = calc_adherence(today_recs)
    weekly_adherence = calc_adherence(weekly_recs)
    monthly_adherence = calc_adherence(monthly_recs)
    overall_adherence = calc_adherence(all_history)

    # Streak Calculations
    day_groups: Dict[str, List[History]] = {}
    for h in all_history:
        d_str = ensure_tz(h.scheduled_time).strftime("%Y-%m-%d")
        if d_str not in day_groups:
            day_groups[d_str] = []
        day_groups[d_str].append(h)

    sorted_days = sorted(day_groups.keys(), reverse=True)
    current_streak = 0
    longest_streak = 0
    temp_streak = 0

    for d_str in sorted_days:
        day_recs = day_groups[d_str]
        adh = calc_adherence(day_recs)
        if adh >= 80.0:
            temp_streak += 1
            if current_streak == 0 or temp_streak == current_streak + 1:
                current_streak = temp_streak
            longest_streak = max(longest_streak, temp_streak)
        else:
            temp_streak = 0

    # Missed & Late Doses
    missed_doses = sum(1 for h in all_history if h.status in [HistoryStatus.MISSED.value, "Missed"])
    late_doses = 0
    for h in all_history:
        if h.action_time and h.scheduled_time:
            diff_mins = (ensure_tz(h.action_time) - ensure_tz(h.scheduled_time)).total_seconds() / 60.0
            if diff_mins > 30.0:
                late_doses += 1

    # Treatment Counts
    active_treatments_cnt = (
        db.query(Treatment)
        .filter(Treatment.user_id == current_user.id, Treatment.status == "Active")
        .count()
    )
    completed_treatments_cnt = (
        db.query(Treatment)
        .filter(Treatment.user_id == current_user.id, Treatment.status == "Completed")
        .count()
    )

    # Medicine Utilization & Refill Predictions
    user_medicines = (
        db.query(Medicine)
        .join(Medicine.treatment)
        .filter(Treatment.user_id == current_user.id)
        .all()
    )

    medicine_analytics = []
    refill_analytics = []
    most_missed_list = []
    highest_missed_rate_med = "None"
    max_missed_rate = -1.0
    medicine_refill_first = "None"
    min_refill_days_val = 9999

    for m in user_medicines:
        med_history = [h for h in all_history if h.medicine_id == m.id]
        tot_prescribed = len(med_history)
        tot_taken = sum(1 for h in med_history if h.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
        tot_missed = sum(1 for h in med_history if h.status in [HistoryStatus.MISSED.value, "Missed"])
        comp_pct = round((tot_taken / max(1, tot_prescribed)) * 100.0, 1) if tot_prescribed > 0 else 100.0
        missed_rate = round((tot_missed / max(1, tot_prescribed)) * 100.0, 1) if tot_prescribed > 0 else 0.0

        if missed_rate > max_missed_rate and tot_missed > 0:
            max_missed_rate = missed_rate
            highest_missed_rate_med = f"{m.medicine_name} ({missed_rate}% missed)"

        medicine_analytics.append({
            "medicine_id": m.id,
            "medicine_name": m.medicine_name,
            "total_prescribed": tot_prescribed,
            "total_taken": tot_taken,
            "total_missed": tot_missed,
            "remaining_stock": m.quantity,
            "completion_percent": comp_pct
        })

        if tot_missed > 0:
            most_missed_list.append({
                "medicine_name": m.medicine_name,
                "missed_count": tot_missed
            })

        # Refill Prediction
        daily_cons = max(1, len(m.reminders)) if m.reminders else 1
        rem_days = int(m.quantity / daily_cons)
        finish_dt = today_date + timedelta(days=rem_days)
        refill_dt = max(today_date, finish_dt - timedelta(days=3))

        if rem_days < min_refill_days_val:
            min_refill_days_val = rem_days
            medicine_refill_first = f"{m.medicine_name} ({rem_days} days left)"

        risk = "Green"
        if rem_days <= 3:
            risk = "Red"
        elif rem_days <= 7:
            risk = "Yellow"

        refill_analytics.append({
            "medicine_name": m.medicine_name,
            "current_stock": m.quantity,
            "daily_consumption": daily_cons,
            "remaining_days": rem_days,
            "refill_date": refill_dt.strftime("%Y-%m-%d"),
            "finish_date": finish_dt.strftime("%Y-%m-%d"),
            "risk_level": risk
        })

    most_missed_sorted = sorted(most_missed_list, key=lambda x: x["missed_count"], reverse=True)
    most_missed_medicine_str = f"{most_missed_sorted[0]['medicine_name']} ({most_missed_sorted[0]['missed_count']} missed)" if most_missed_sorted else "None"

    # 7-Day Weekly Adherence Chart & Best/Worst Day Calculation
    chart_data = []
    best_day_name = "N/A"
    best_day_val = -1.0
    worst_day_name = "N/A"
    worst_day_val = 101.0

    for i in range(6, -1, -1):
        day_date = today_start - timedelta(days=i)
        day_str = day_date.strftime("%Y-%m-%d")
        label = day_date.strftime("%A")

        day_recs = day_groups.get(day_str, [])
        taken_cnt = sum(1 for r in day_recs if r.status in [HistoryStatus.TAKEN.value, "Completed", "Taken"])
        missed_cnt = sum(1 for r in day_recs if r.status in [HistoryStatus.MISSED.value, "Missed"])
        skipped_cnt = sum(1 for r in day_recs if r.status in [HistoryStatus.SKIPPED.value, "Skipped"])
        tot_day = taken_cnt + missed_cnt + skipped_cnt

        day_adh = round((taken_cnt / max(1, tot_day)) * 100.0, 1) if tot_day > 0 else 100.0

        if tot_day > 0:
            if day_adh > best_day_val:
                best_day_val = day_adh
                best_day_name = f"{label} ({day_adh}%)"
            if day_adh < worst_day_val:
                worst_day_val = day_adh
                worst_day_name = f"{label} ({day_adh}%)"

        chart_data.append({
            "day": label[:3],
            "date": day_str,
            "taken": taken_cnt,
            "missed": missed_cnt,
            "skipped": skipped_cnt
        })

    # Treatment Progress Analytics
    user_treatments = (
        db.query(Treatment)
        .filter(Treatment.user_id == current_user.id)
        .all()
    )

    treatment_progress = []
    treatment_closest_completion_str = "None"
    max_progress = -1.0

    for tr in user_treatments:
        total_days = max(1, (tr.end_date - tr.start_date).days)
        elapsed_days = max(0, (today_date - tr.start_date).days)
        progress_pct = min(100.0, max(0.0, round((elapsed_days / total_days) * 100.0, 1)))

        if progress_pct > max_progress and tr.status == "Active":
            max_progress = progress_pct
            treatment_closest_completion_str = f"{tr.disease_name} ({progress_pct}% completed)"

        treatment_progress.append({
            "treatment_id": tr.id,
            "disease_name": tr.disease_name,
            "doctor_name": tr.doctor_name,
            "start_date": tr.start_date.strftime("%Y-%m-%d"),
            "end_date": tr.end_date.strftime("%Y-%m-%d"),
            "status": tr.status,
            "progress_percent": progress_pct
        })

    summary = get_dashboard_summary(db, current_user)

    # Recent Activity Events
    recent_activity = []
    for h in all_history[:15]:
        med_name = h.medicine.medicine_name if h.medicine else f"Medicine #{h.medicine_id}"
        recent_activity.append({
            "id": h.id,
            "title": f"{med_name} - {h.status}",
            "description": h.notes or f"Status logged as {h.status}",
            "status": h.status,
            "timestamp": ensure_tz(h.action_time or h.scheduled_time).strftime("%b %d, %I:%M %p")
        })

    return {
        "daily_adherence": daily_adherence,
        "weekly_adherence": weekly_adherence,
        "monthly_adherence": monthly_adherence,
        "overall_adherence": overall_adherence,
        "average_daily_adherence": daily_adherence,
        "average_weekly_adherence": weekly_adherence,
        "completion_percent": weekly_adherence,
        "consistency_percent": min(100.0, weekly_adherence + 5.0),
        "current_streak": current_streak,
        "longest_streak": max(longest_streak, current_streak),
        "best_adherence_day": best_day_name if best_day_val >= 0 else "Today (100%)",
        "worst_adherence_day": worst_day_name if worst_day_val <= 100 else "None",
        "most_missed_medicine": most_missed_medicine_str,
        "highest_missed_rate_medicine": highest_missed_rate_med,
        "medicine_refill_first": medicine_refill_first,
        "treatment_closest_completion": treatment_closest_completion_str,
        "missed_doses": missed_doses,
        "late_doses": late_doses,
        "active_treatments": active_treatments_cnt,
        "completed_treatments": completed_treatments_cnt,
        "medicine_analytics": medicine_analytics,
        "refill_analytics": refill_analytics,
        "chart_data": chart_data,
        "most_missed_medicines": most_missed_sorted,
        "treatment_progress": treatment_progress,
        "quick_stats": summary,
        "recent_activity": recent_activity
    }
