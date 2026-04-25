import csv
import os
from django.conf import settings
import threading
from django.utils import timezone
from .models import CheckIn
from datetime import date, timedelta
from django.db.models import Avg, Sum
from .forms import MOOD_MAP, likert_round

# Utility functions for date handling
today = timezone.localdate()
start_of_week = today - timedelta(days=today.weekday() + 1 if today.weekday() < 6 else 0)
end_of_week = start_of_week + timedelta(days=6)
max_days = 7

# Reverse mapping for mood scores to mood keys
REVERSE_MOOD_MAP = {v: k for k, v in MOOD_MAP.items()}

# Defined activity fields
ACTIVITY_FIELDS = ["walking", "running", "cycling", "gym", "sport", "others"]
MAX_DAILY_INTENSITY = 4 * len(ACTIVITY_FIELDS) 

# Thread lock to make CSV writes safe
csv_lock = threading.Lock()

# Function to append check-in data to a CSV file
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

# Function to calculate the total activity intensity for a given user and day
def get_daily_activity_intensity(user, day):
    activity_aggregate = (
        CheckIn.objects
        .filter(user=user, created_at__date=day)
        .aggregate(**{f: Sum(f) for f in ACTIVITY_FIELDS})
    )

    raw_total = sum((activity_aggregate[f] or 0) for f in ACTIVITY_FIELDS)

    # Maximum cap for achievable intensity per day
    return min(raw_total, MAX_DAILY_INTENSITY)

# Function to calculate mood data for each day of the current week
def calculate_week_days(user):
    week_days = []

    for i in range(max_days):
        day = start_of_week + timedelta(days=i)
        
        # Calculate average mood score for the day
        avg_score = (
            CheckIn.objects.filter(user=user, created_at__date=day)
            .aggregate(avg_score=Avg('mood_score'))['avg_score']
        )

        rounded_score = likert_round(avg_score)
        mood_key = REVERSE_MOOD_MAP.get(rounded_score)

        # Calculate total activity intensity for the day
        daily_intensity_agg = get_daily_activity_intensity(user, day)
        activity_intensity_report = (daily_intensity_agg / MAX_DAILY_INTENSITY) *100 if MAX_DAILY_INTENSITY > 0 else 0

        week_days.append({
            "label": day.strftime("%a"),
            "month": day.strftime("%b"),
            "date": day.strftime("%d"),
            "is_today": (day == today),
            "mood": mood_key,
            "mood_score": rounded_score,
            "activity_intensity": daily_intensity_agg,
            "activity_intensity_report": activity_intensity_report,
        })

    return week_days

# Function to calculate the current streak of consecutive check-in days
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

# Function to get lifetime and weekly check-in counts, and whether the user has checked in today
def get_lifetime_weekly_checkin_count(user):
    # Lifetime unique check-in days
    lifetime_checkins_days = CheckIn.objects.filter(user=user).values('created_at__date').distinct().count()

    # Weekly check-ins this week
    total_weekly_checkins = CheckIn.objects.filter(
                        user=user,
                        created_at__date__range=(start_of_week, end_of_week)
                    ).count()
    
    # Count of unique days with check-ins this week
    weekly_day_count = CheckIn.objects.filter(
                        user=user,
                        created_at__date__range=(start_of_week, end_of_week)
                    ).values('created_at__date').distinct().count()
    
    # Has the user checked in today?
    has_checked_in_today = CheckIn.objects.filter(
        user=user,
        created_at__date=today
    ).exists()

    return lifetime_checkins_days, total_weekly_checkins, weekly_day_count, has_checked_in_today

# Function to generate a streak summary message based on the user's check-in history
def get_streak_summary(user):
    streak = calculate_streak(user)

    lifetime_checkins_days, total_weekly_checkins, weekly_day_count, has_checked_in_today = get_lifetime_weekly_checkin_count(user)

    # First-ever check-in for new users
    if lifetime_checkins_days == 1 and has_checked_in_today:
        return "🌱 Welcome! Great start to your first mood check-In🔥"

    if lifetime_checkins_days > 1 and weekly_day_count == 1 and has_checked_in_today:
        return "🌿 Fresh start — Can you beat another weekly streak?"
    
    # User has previous check-ins but none today
    if not has_checked_in_today and weekly_day_count > 0 and streak == 0:
        return "👋 Haven’t checked in today — take a moment to check-In how you're feeling"

    if streak <= 0:
        return "💛 Be kind to yourself today — check-In to track your mood patterns"
    
    if streak == 1:
        return "✨ Nice to see you check-In in again — awareness builds clarity"
    
    if streak == 2:
        return f"✨ {streak} days streak of mood awareness — you're building a helpful habit"

    if streak >= 3 and streak < 6:
        return f"🌿 {streak} days streak of consistent check-In — great self-awareness"
    
    if streak >= 6:
        return f"🌟 {streak} days streak of tuning into your mood — you're really in tune with yourself"

    return f"🌿 {streak} days streak of mood check-In — keep noticing how you feel"