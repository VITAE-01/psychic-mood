from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import CheckInForm
from .utils import append_checkin_to_csv
from .models import CheckIn
from django.utils import timezone
from datetime import date, timedelta


# Create your views here.
@login_required
@never_cache
def dashboard_index(request):
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday() + 1)

    week_days = []
    for i in range(7):
        day = start_of_week + timedelta(days=i)
        week_days.append({
            "label": day.strftime("%a"),
            "month": day.strftime("%b"),
            "date": day.strftime("%d"),
            "is_today": (day == today)
        })

    context = {
        "week_days": week_days,
    }

    return render(request, 'dashboard/dashboard_index.html', context)

def submit_checkin(request):
    if request.method == "POST":
        form = CheckInForm(request.POST)

        if form.is_valid():
            last_checkin = CheckIn.objects.filter(user=request.user).order_by("-created_at").first()

            if last_checkin:
                gap = timezone.now() - last_checkin.created_at

                if gap < timedelta(hours=6):
                    next_allowed = last_checkin.created_at + timedelta(hours=6)
                    remaining = next_allowed - timezone.now()

                    hours = remaining.seconds // 3600
                    minutes = (remaining.seconds % 3600) // 60

                    return JsonResponse({
                        "status": "blocked",
                        "message": f"You already submitted a check-in recently. "
                                    f"Next check-in available in {hours}h {minutes}m."
                    })

            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.save()

            # Export to CSV
            append_checkin_to_csv(checkin)

            return JsonResponse({"status": "ok"})

    return JsonResponse({"status": "error"})