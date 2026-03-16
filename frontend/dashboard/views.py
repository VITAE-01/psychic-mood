from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .forms import CheckInForm
from .utils import append_checkin_to_csv



# Create your views here.
@login_required
@never_cache
def dashboard_index(request):
    return render(request, 'dashboard/dashboard_index.html')

def submit_checkin(request):
    if request.method == "POST":
        form = CheckInForm(request.POST)
        if form.is_valid():
            checkin = form.save(commit=False)
            checkin.user = request.user
            checkin.save()

            # Export to CSV
            append_checkin_to_csv(checkin)

        return redirect('dashboard:index')

    return redirect('dashboard:index')