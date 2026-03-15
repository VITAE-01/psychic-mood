from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# Create your views here.
@login_required
@never_cache
def dashboard_index(request):
    return render(request, 'dashboard/dashboard_index.html')

def activity_checkin(request):
    if request.method == 'POST':
        activity_type = request.POST.get('activity_type')
        duration = request.POST.get('duration')
        mood = request.POST.get('mood')

        # Save to database here...

        return redirect('dashboard:index')

    return redirect('dashboard:index')