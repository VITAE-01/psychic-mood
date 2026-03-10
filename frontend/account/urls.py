from django.urls import path
from . import views


app_name = "account"

urlpatterns = [
    path('register/', views.signup, name='register'),
    # path('verify-email/', views.verify_email, name='verify-email'),
    path('create-password/', views.create_password, name='create-password'),
    path('login/', views.login_view, name='login'),
    path('profile/', views.profile, name='profile'),
    # path('profile/change-password/', views.forgot_password, name='change-password'),
    path('profile/edit/', views.edit_profile, name='edit-profile'),
    path('forgot-password/', views.forgot_password, name='forgot-password'),
    path('reset-password/', views.reset_password, name='reset-password'),
    path('logout/', views.logout_view, name='logout'),
]