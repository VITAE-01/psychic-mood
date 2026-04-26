from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('submit-checkin/', views.submit_checkin, name='submit_checkin'),
    path('week-data/', views.week_data, name="week_data"),
]