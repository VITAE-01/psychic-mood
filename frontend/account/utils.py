import csv
import os
import threading
from django.conf import settings
from django.utils import timezone

# Thread lock to make CSV writes safe
csv_lock = threading.Lock()


def write_active_user_to_csv(user):
    """
    Append only active users (password created) to a CSV file in a thread-safe way.
    Username is anonymized for privacy.
    """
    if not user.is_active:
        return

    file_path = os.path.join(settings.BASE_DIR, 'active_users.csv')

    # Acquire lock before writing
    with csv_lock:
        file_exists = os.path.isfile(file_path)

        with open(file_path, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)

            # Write header if file does not exist
            if not file_exists:
                writer.writerow([
                    'user_id', 'age_range', 'gender', 'height', 'weight',
                    'is_active', 'registered_at'
                ])

            # Human-readable timestamp
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            writer.writerow([
                user.id,
                user.age_range,
                user.gender,
                user.height,
                user.weight,
                user.is_active,
                timestamp
            ])