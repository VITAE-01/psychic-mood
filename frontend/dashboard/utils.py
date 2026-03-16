import csv
import os
from django.conf import settings
import threading
from django.utils import timezone

# Thread lock to make CSV writes safe
csv_lock = threading.Lock()

def append_checkin_to_csv(checkin):
    # Path to your CSV file (e.g., dashboard/data/checkins.csv)
    file_path = os.path.join(settings.BASE_DIR, "activity_checkins.csv")

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
            "created_at": timestamp
        }

        # Write to CSV
        with open(file_path, "a", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=row.keys())

            # Write header only once
            if not file_exists:
                writer.writeheader()

            writer.writerow(row)