from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache

# Create your views here.
@login_required
@never_cache
def dashboard_index(request):
    return render(request, 'dashboard/dashboard_index.html')