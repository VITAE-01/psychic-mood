from django.shortcuts import render
from django.http import HttpResponse


# Create your views here.
# /account -> index view will be called when the user visits the account page.
def index(request):
    return HttpResponse("This is the landing page.")


def signup(request):
    return HttpResponse("This is the signup page.")


def verify_email(request):
    return HttpResponse("This is the email verification page.")


def create_password(request):
    return HttpResponse("This is the create password page.")


def login(request):
    return HttpResponse("This is the login page.")


def profile(request):
    return HttpResponse("This is the profile page.")


def edit_profile(request):
    return HttpResponse("This is the edit profile page.")


def forgot_password(request):
    return HttpResponse("This is the forgot password page.")


def logout_view(request):
    return HttpResponse("This is the logout page.")