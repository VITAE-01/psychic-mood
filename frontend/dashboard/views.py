from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import CheckInForm
from .utils import append_checkin_to_csv, calculate_week_days, get_streak_summary, get_lifetime_weekly_checkin_count
from .models import CheckIn
from django.utils import timezone
from datetime import date, datetime, timedelta


@login_required
@never_cache
def dashboard_index(request):
    week_days = calculate_week_days(user=request.user)
    summary = get_streak_summary(user=request.user)
    lifetime_checkins_days, first_checkin_date, total_weekly_checkins, weekly_day_count, has_checked_in_today = get_lifetime_weekly_checkin_count(user=request.user)

    context = {
        "week_days": week_days,
        "streak": summary,
        "weekly_unique_days": weekly_day_count,
        "has_checked_in_today": has_checked_in_today,
        "first_checkin_date": first_checkin_date,
        "today": timezone.localdate()
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

def week_data(request):
    user = request.user
    start = request.GET.get("start")

    if start:
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d").date()
        except ValueError:
            return JsonResponse({"error": "Invalid date"}, status=400)
    else:
        start_date = None

    week_days = calculate_week_days(user, start_date)

    return JsonResponse({"week_days": week_days})