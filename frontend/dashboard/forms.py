from django import forms
from .models import CheckIn

MOOD_MAP = {
    "low": 1,
    "stressed": 2,
    "okay": 3,
    "fulfilled": 4,
    "energized": 5
}

def likert_round(value):
    if value is None:
        return None
    decimal = value - int(value)
    if decimal < 0.5:
        return int(value)
    return int(value) + 1

ACTIVITY_DURATION_MAP = {
    0: "No activity",
    1: "0–15 mins",
    2: "15–30 mins",
    3: "30–45 mins",
    4: "45 mins+"
}

def map_intensity_to_duration(total):
    if total <= 0:
        return "No activity"
    if total == 1:
        return "0–15 mins"
    if total == 2:
        return "15–30 mins"
    if total == 3:
        return "30–45 mins"
    return "45 mins+"

HBM_INTERPRETATION = {
    "strong_negative": {
        "activity": "You were active today despite strong perceived barriers to being active.",
        "no_activity": "Strong perceived barriers likely prevented you from being active today."
    },

    "weak_negative": {
        "activity": "You were active today even though some perceived barriers were present.",
        "no_activity": "Some perceived barriers may have prevented you from being active today."
    },

    "neutral": {
        "activity": "Your beliefs about activity were fairly balanced today between benefits, barriers, and confidence.",
        "no_activity": "Your beliefs about activity were fairly balanced today between benefits, barriers, and confidence."
    },

    "weak_positive_pb": {
        "activity": "You were active today while recognizing some benefits of being active.",
        "no_activity": "Your beliefs leaned slightly toward the benefits of being active today."
    },

    "weak_positive_se": {
        "activity": "You were active today with some confidence in your ability to be active.",
        "no_activity": "Your beliefs leaned slightly toward confidence in being active today."
    },

    "strong_positive_pb": {
        "activity": "You were active today with a strong belief in the benefits of being active.",
        "no_activity": "Your beliefs strongly emphasized the benefits of being active today."
    },

    "strong_positive_se": {
        "activity": "You were active today with strong confidence in your ability to be active.",
        "no_activity": "Your beliefs strongly emphasized confidence in being active today."
    }
}


class CheckInForm(forms.ModelForm):
    class Meta:
        model = CheckIn
        fields = [
            'perceived_benefits',
            'self_efficacy',
            'barrier_time',
            'barrier_tired',
            'barrier_others',
            'performed_activity',
            'walking', 'running', 'cycling', 'gym', 'sport', 'others',
            'mood',
        ]

    def save(self, commit=True):
        instance = super().save(commit=False)

        instance.mood_score = MOOD_MAP.get(instance.mood)

        if commit:
            instance.save()

        return instance