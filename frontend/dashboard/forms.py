from django import forms
from .models import CheckIn

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