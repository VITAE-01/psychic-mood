import csv
import os
from django.conf import settings
import threading
from django.utils import timezone
from .models import CheckIn
from datetime import date, timedelta
from django.db.models import Avg
from .forms import MOOD_MAP, likert_round

# Utility functions for date handling
today = timezone.localdate()
start_of_week = today - timedelta(days=today.weekday() + 1 if today.weekday() < 6 else 0)
max_days = 7
REVERSE_MOOD_MAP = {v: k for k, v in MOOD_MAP.items()}

# Thread lock to make CSV writes safe
csv_lock = threading.Lock()

def append_checkin_to_csv(checkin):
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    DATA_DIR = os.path.join(BASE_DIR, "data")
    os.makedirs(DATA_DIR, exist_ok=True)

    file_path = os.path.join(DATA_DIR, "activity_checkins.csv")

    with csv_lock:
        file_exists = os.path.isfile(file_path)

        # Human-readable timestamp
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

        # Prepare row data
        row = {
            "user_id": checkin.user.id,
            "perceived_benefits": checkin.perceived_benefits,
            "self_efficacy": checkin.self_efficacy,
            "barrier_time": checkin.barrier_time,
            "barrier_tired": checkin.barrier_tired,
            "barrier_others": checkin.barrier_others,
            "performed_activity": checkin.performed_activity,
            "walking": checkin.walking,
            "running": checkin.running,
            "cycling": checkin.cycling,
            "gym": checkin.gym,
            "sport": checkin.sport,
            "others": checkin.others,
            "mood": checkin.mood,
            "mood_score": checkin.mood_score,
            "created_at": timestamp
        }

        # Write to CSV
        with open(file_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())

            # Write header only once
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)

def calculate_week_days(user):
    week_days = []

    for i in range(max_days):
        day = start_of_week + timedelta(days=i)
        
        avg_score = (
            CheckIn.objects.filter(user=user, created_at__date=day)
            .aggregate(avg_score=Avg('mood_score'))['avg_score']
        )

        rounded_score = likert_round(avg_score)
        mood_key = REVERSE_MOOD_MAP.get(rounded_score)
        
        week_days.append({
            "label": day.strftime("%a"),
            "month": day.strftime("%b"),
            "date": day.strftime("%d"),
            "is_today": (day == today),
            "mood": mood_key,
            "mood_score": rounded_score,
        })
    return week_days

def calculate_streak(user, max_days=7):
    start_date = today - timedelta(days=max_days - 1)

    # Fetch all check-ins in one go
    checkins = CheckIn.objects.filter(
        user=user,
        created_at__date__gte=start_date
    ).values_list('created_at__date', flat=True)

    checkin_dates = set(checkins)

    streak = 0

    for i in range(max_days):
        day = today - timedelta(days=i)

        if day in checkin_dates:
            streak += 1
        else:
            break

    return streak

def get_streak_summary(user):
    streak = calculate_streak(user)
    total_checkins = CheckIn.objects.filter(user=user).count()

    # Has the user checked in today?
    has_checked_in_today = CheckIn.objects.filter(
        user=user,
        created_at__date=today
    ).exists()

    if total_checkins == 1 and has_checked_in_today:
        return "🎉 Welcome! — Great start, keep it going!"
    
    # User has previous check-ins but none today
    if not has_checked_in_today and total_checkins > 0:
        return "👋 You haven’t checked in today — log activity to keep your streak alive."

    if streak <= 0:
        return "😴! Try to engage in some physical activity today!"
    
    if streak == 1:
        return "👍 Welcome back — Great to see you checkin in again."
    
    if streak == 2:
        return f"👍 {streak} day{'s' if streak != 1 else ''} of activity! Keep going!"

    if streak >= 3 and streak < 6:
        return f"🔥 {streak} day{'s' if streak != 1 else ''} streak! Keep it up!"
    
    if streak >= 6:
        return f"🔥 {streak} day{'s' if streak != 1 else ''} streak! You're on fire!"

    summary = f"🔥 {streak} day{'s' if streak != 1 else ''} streak!"

    return summary