from django.db import models
from django.conf import settings


class CheckIn(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    perceived_benefits = models.IntegerField(null=True, blank=True)
    self_efficacy = models.IntegerField(null=True, blank=True)
    barrier_time = models.IntegerField(null=True, blank=True)
    barrier_tired = models.IntegerField(null=True, blank=True)
    barrier_others = models.IntegerField(null=True, blank=True)

    performed_activity = models.CharField(max_length=10, choices=[
        ('yes', 'Yes'),
        ('no', 'No'),
    ])

    # Activity fields (optional if performed_activity = no)
    walking = models.CharField(max_length=50, blank=True, null=True)
    running = models.CharField(max_length=50, blank=True, null=True)
    cycling = models.CharField(max_length=50, blank=True, null=True)
    gym = models.CharField(max_length=50, blank=True, null=True)
    sport = models.CharField(max_length=50, blank=True, null=True)
    others = models.CharField(max_length=50, blank=True, null=True)

    # Mood
    mood = models.CharField(max_length=20)
    mood_score = models.IntegerField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} check‑in on {self.created_at.strftime('%Y-%m-%d %H:%M')}"