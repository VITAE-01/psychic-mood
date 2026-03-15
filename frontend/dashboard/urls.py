from django.urls import path
from . import views

app_name = "dashboard"

urlpatterns = [
    path('', views.dashboard_index, name='index'),
    path('checkin/', views.activity_checkin, name='activity_checkin'),
]