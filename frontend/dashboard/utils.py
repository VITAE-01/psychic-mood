import csv
import os
import threading
from django.utils import timezone
from .models import CheckIn
from datetime import datetime, timedelta
from django.db.models import Avg, F
import numpy as np
from .forms import MOOD_MAP, HBM_INTERPRETATION, map_intensity_to_duration, likert_round

# Utility functions for date handling
def get_week_range(reference_date=None):
    if reference_date is None:
        reference_date = timezone.localdate()

    today = timezone.localdate()
    max_days = 7
    days_since_sunday = (reference_date.weekday() + 1) % max_days
    start_of_week = reference_date - timedelta(days=days_since_sunday)
    end_of_week = start_of_week + timedelta(days=6)

    return today, start_of_week, end_of_week, max_days

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

# Function to calculate the BBI threshold values (Q1, Median and Q3) for a given user
def calc_belief_balance_index_threshold(user):
    BBI_EPSILON = 1e-6  # avoid division by zero
    belief_balance_index_values = []

    checkins = list(
        CheckIn.objects.filter(user=user)
        .order_by("created_at")
        .values(
            "created_at",
            "perceived_benefits",
            "self_efficacy",
            "barrier_tired",
            "barrier_time",
            "barrier_others",
        )
    )

    if not checkins:
        return None, None, None
    
    daily_entries = {}
    for entry in checkins:
        day = entry["created_at"].date()
        if day not in daily_entries:
            daily_entries[day] = entry

    for entry in daily_entries.values():

        perceived_benefits = int(entry["perceived_benefits"] or 0)
        self_efficacy = int(entry["self_efficacy"] or 0)

        barrier_tired = int(entry["barrier_tired"] or 0)
        barrier_time = int(entry["barrier_time"] or 0)
        barrier_others = int(entry["barrier_others"] or 0)

        barrier_composite = barrier_tired + barrier_time + barrier_others

        if (perceived_benefits + self_efficacy + barrier_composite) == 0:
            continue

        numerator = (perceived_benefits + self_efficacy) - barrier_composite
        denominator = (perceived_benefits + self_efficacy) + barrier_composite + BBI_EPSILON

        belief_balance_index = round((numerator / denominator), 2)
        belief_balance_index_values.append(belief_balance_index)

    if len(belief_balance_index_values) < 4 :  # Not enough data points to calculate meaningful quartiles
        return None, None, None
    
    # Calculate Q1, Median and Q3 using numpy's percentile function
    q1 = round((float(np.percentile(belief_balance_index_values, 25))), 2)
    q3 = round((float(np.percentile(belief_balance_index_values, 75))), 2)
    median = float(np.percentile(belief_balance_index_values, 50))


    return q1, median, q3

# Function to calculate the belief values for a given user and day
def get_daily_belief_summary(user, day):
    BBI_EPSILON = 1e-6  # avoid division by zero

    try:
        entry = CheckIn.objects.filter(user=user, created_at__date=day).first()
    except CheckIn.DoesNotExist:
        return {
            "perceived_benefits": None,
            "self_efficacy": None,
            "barrier_composite": None,
            "belief_balance_index": None,
        }

    perceived_benefits = int(getattr(entry, "perceived_benefits", 0) or 0)
    self_efficacy = int(getattr(entry, "self_efficacy", 0) or 0)

    barrier_tired = int(getattr(entry, "barrier_tired", 0) or 0)
    barrier_time = int(getattr(entry, "barrier_time", 0) or 0)
    barrier_others = int(getattr(entry, "barrier_others", 0) or 0)

    barrier_composite = barrier_tired + barrier_time + barrier_others

    # Compute BBI (range: -1 to +1)
    numerator = (perceived_benefits + self_efficacy) - barrier_composite
    denominator = (perceived_benefits + self_efficacy) + barrier_composite + BBI_EPSILON

    daily_belief_balance_index = round((numerator / denominator), 2)

    return {
        "perceived_benefits": perceived_benefits,
        "self_efficacy": self_efficacy,
        "barrier_composite": barrier_composite,
        "daily_belief_balance_index": daily_belief_balance_index,
    }

# Function to classify the daily BBI into categories based on Q1, median and Q3 thresholds
def classify_daily_hbm(bbi, q1, median, q3):

    if bbi is None or q1 is None or median is None or q3 is None:
        return "no_data"

    if bbi < q1:
        return "strong_negative"

    if q1 <= bbi < median:
        return "weak_negative"

    if abs(bbi - median) < 1e-6:
        return "neutral"

    if median < bbi <= q3:
        return "weak_positive"

    if bbi > q3:
        return "strong_positive"

# Function to calculate the total activity intensity for a given user and day
def get_daily_activity_summary(user, day):
    activity_aggregate = CheckIn.objects.filter(
        user=user,
        created_at__date=day
    )

    # Initialise breakdown for each activity type
    breakdown = {field: 0 for field in ACTIVITY_FIELDS}

    # Sum intensities across multiple entries
    for entry in activity_aggregate:
        for field in ACTIVITY_FIELDS:
            raw_value = getattr(entry, field, 0) or 0

            try:
                value = int(raw_value or 0)
            except ValueError:
                value = 0

            breakdown[field] += value

    # Map intensity to bucket duration interval for readability
    readable_breakdown = {
        field: map_intensity_to_duration(breakdown[field])
        for field in ACTIVITY_FIELDS
    }

    # Total intensity for the day per day
    raw_total = sum(breakdown.values())

    # Maximum achievable intensity per day to prevent outliers
    capped_total = min(raw_total, MAX_DAILY_INTENSITY)

    activity_intensity_report = round((capped_total / MAX_DAILY_INTENSITY) * 100, 2 )if MAX_DAILY_INTENSITY > 0 else 0

    return {
        "activity_breakdown": readable_breakdown,
        "intensity_percent": activity_intensity_report
    }

# Main function to generate the daily HBM summary for a given user and day, using the BBI thresholds
def get_daily_hbm_summary(user, day, q1, median, q3):
    belief = get_daily_belief_summary(user, day)
    bbi = belief["daily_belief_balance_index"]
    
    if bbi is None:
        return None

    # Get belief summary
    pb = belief["perceived_benefits"] or 0
    se = belief["self_efficacy"] or 0
    dominance = "pb" if pb > se else "se"

    # Get activity summary
    activity_summary = get_daily_activity_summary(user, day)
    did_activity = activity_summary["intensity_percent"] > 0
    activity_key = "activity" if did_activity else "no_activity"

    # HBM classification
    hbm_class = classify_daily_hbm(bbi, q1, median, q3)

    # --- Step 6: Map to interpretation key ---
    if hbm_class == "no_data":
        interp_key = "no_data"
    
    elif hbm_class in ["strong_negative", "weak_negative", "neutral"]:
        interp_key = hbm_class
    else:
        # positive tiers depend on PB vs SE dominance
        interp_key = f"{hbm_class}_{dominance}"

    # --- Step 8: Return the final interpretation sentence ---
    return HBM_INTERPRETATION.get(interp_key, {}).get(activity_key)

# Function to calculate mood data for each day of the current week
def calculate_week_days(user, start_date=None):
    today, start_of_week, end_of_week, max_days = get_week_range(start_date)
    q1, median, q3 = calc_belief_balance_index_threshold(user)
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

        # Calculate total activity summary and intensity for the day
        activity_summary = get_daily_activity_summary(user, day)

        daily_hbm_summary = get_daily_hbm_summary(user, day, q1, median, q3)

        week_days.append({
            "label": day.strftime("%a"),
            "month": day.strftime("%b"),
            "year": day.strftime("%Y"),
            "date": day.strftime("%d"),
            "iso_date": day.isoformat(),
            "is_today": (day == today),
            "daily_hbm_summary": daily_hbm_summary,
            "mood": mood_key,
            "mood_score": rounded_score,
            "activity_breakdown": activity_summary["activity_breakdown"],
            "activity_intensity_report": activity_summary["intensity_percent"],
        })
    return week_days

# Function to calculate the current streak of consecutive check-in days
def calculate_streak(user, max_days=7):
    today, start_of_week, end_of_week, max_days = get_week_range()
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
    today, start_of_week, end_of_week, max_days = get_week_range()
    # Lifetime unique check-in days
    lifetime_checkins_days = CheckIn.objects.filter(user=user).values('created_at__date').distinct().count()

    # First checkin from user
    first_checkin = CheckIn.objects.filter(user=user).order_by("created_at").first()
    if first_checkin:
        first_checkin_date = first_checkin.created_at.date()
    else:
        first_checkin_date = timezone.localdate()

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

    return lifetime_checkins_days, first_checkin_date, total_weekly_checkins, weekly_day_count, has_checked_in_today

# Function to generate a streak summary message based on the user's check-in history
def get_streak_summary(user):
    streak = calculate_streak(user)

    lifetime_checkins_days, first_checkin_date, total_weekly_checkins, weekly_day_count, has_checked_in_today = get_lifetime_weekly_checkin_count(user)

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

# Function to calculate the average mood score and activity intensity for the current week
def get_weekly_activity_mood_averages(user, start_date=None):
    today, start_of_week, end_of_week, max_days = get_week_range(start_date)

    # Mood
    mood_avg = (
        CheckIn.objects.filter(
            user=user,
            created_at__date__gte=start_of_week,
            created_at__date__lte=end_of_week
        ).aggregate(avg=Avg("mood_score"))["avg"]
    )

    # Activity (intensity percent)
    weekly_activity_aggregate = CheckIn.objects.filter(
        user=user,
        created_at__date__gte=start_of_week,
        created_at__date__lte=end_of_week
    )

    # Initialise breakdown for each activity type
    breakdown = {field: 0 for field in ACTIVITY_FIELDS}

    # Sum intensities across multiple entries
    for entry in weekly_activity_aggregate:
        for field in ACTIVITY_FIELDS:
            raw_value = getattr(entry, field, 0) or 0

            try:
                value = int(raw_value or 0)
            except ValueError:
                value = 0

            breakdown[field] += value

    if weekly_activity_aggregate:
        activity_avg = sum(breakdown.values()) / len(weekly_activity_aggregate)
    else:
        activity_avg = None

    return {
        "weekly_mood_avg": mood_avg,
        "weekly_activity_avg": activity_avg
    }

def relative_change(current, previous):
    if current is None or previous is None or previous == 0:
        return None
    return (current - previous) / previous

def classify_weekly_change(delta):
    if delta is None:
        return { "color": "secondary", "magnitude": None}

    if delta == 0:
        return {"color": "secondary", "magnitude": "none"}

    color = "success" if delta > 0 else "danger"
    abs_delta = abs(delta)

    # cohens thresholds for small, medium, large effects size
    if abs_delta < 0.10:
        magnitude = "xs"
    elif abs_delta < 0.30:
        magnitude = "sm"
    elif abs_delta < 0.50:
        magnitude = "md"
    else:
        magnitude = "lg"

    return {
        "color": color,
        "magnitude": magnitude,
    }

def get_weekly_trend(user, start_of_week):
    # Current week
    current = get_weekly_activity_mood_averages(user, start_of_week)

    # Previous week
    prev_week_start = start_of_week - timedelta(days=7)
    previous = get_weekly_activity_mood_averages(user, prev_week_start)

    # Compute deltas
    delta_mood = relative_change(current["weekly_mood_avg"], previous["weekly_mood_avg"])
    delta_activity = relative_change(current["weekly_activity_avg"], previous["weekly_activity_avg"])

    # Classify
    mood_direction = classify_weekly_change(delta_mood)
    activity_direction = classify_weekly_change(delta_activity)

    if previous["weekly_mood_avg"] is None or previous["weekly_activity_avg"] is None:
        return {
        "current_week_mood": round(current["weekly_mood_avg"], 2) if current["weekly_mood_avg"] else None,
        "previous_week_mood": None,
        "current_week_activity": round(current["weekly_activity_avg"], 2) if current["weekly_activity_avg"] else None,
        "previous_week_activity": None,
        "delta_mood": 0.00,
        "delta_activity": 0.00,
        "mood_color": "secondary",
        "mood_magnitude": "baseline",
        "activity_color": "secondary",
        "activity_magnitude": "baseline",
        }

    trend = {
        "current_week_mood": round((current["weekly_mood_avg"]), 2) if current["weekly_mood_avg"] else None,
        "previous_week_mood": round((previous["weekly_mood_avg"]), 2) if previous["weekly_mood_avg"] else None,
        "current_week_activity": round((current["weekly_activity_avg"]), 2) if current["weekly_activity_avg"] else None,
        "previous_week_activity": round((previous["weekly_activity_avg"]), 2) if previous["weekly_activity_avg"] else None,
        "delta_mood": round((delta_mood), 2) if delta_mood is not None else None,
        "delta_activity": round((delta_activity), 2) if delta_activity is not None else None,
        "mood_color": mood_direction["color"],
        "mood_magnitude": mood_direction["magnitude"],
        "activity_color": activity_direction["color"],
        "activity_magnitude": activity_direction["magnitude"],
    }
    return trend