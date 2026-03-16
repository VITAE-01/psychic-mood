from django import forms
from .models import CheckIn

MOOD_MAP = {
    "low": 1,
    "stressed": 2,
    "okay": 3,
    "fulfilled": 4,
    "energized": 5
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