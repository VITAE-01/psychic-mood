from django.urls import path
from . import views


urlpatterns = [
    path('register/', views.signup),
    path('verify-email/', views.verify_email),
    path('create-password/', views.create_password),
    path('login/', views.login),
    path('profile/', views.profile),
    path('profile/change-password/', views.forgot_password),
    path('profile/edit/', views.edit_profile),
    path('forgot-password/', views.forgot_password),
    path('logout/', views.logout_view, name='logout'),
]