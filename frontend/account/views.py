from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Account
from .forms import RegisterForm
from .forms import CreatePasswordForm
from .forms import LoginForm
from .forms import ForgotPasswordForm
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .utils import write_active_user_to_csv


User = get_user_model()


# Create your views here.
# /account -> index view will be called when the user visits the account page.
def index(request):
    return HttpResponse("This is the landing page.")

def signup(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.set_unusable_password()   # important
            user.is_active = False         # until email verification
            user.save()

            request.session["registration_email"] = user.email

            return redirect("account:create-password")

    else:
        form = RegisterForm()

    return render(request, "account/register.html", {"form": form})


# def verify_email(request):
#     return HttpResponse("This is the email verification page.")


def create_password(request):

    if request.method == "POST":
        form = CreatePasswordForm(request.POST)

        if form.is_valid():

            email = request.session.get("registration_email")

            user = User.objects.get(email=email)

            user.set_password(form.cleaned_data["password1"])
            user.is_active = True
            user.save()

            # --- Log user to CSV only after password is set ---
            write_active_user_to_csv(user)

            return redirect("account:login")

    else:
        form = CreatePasswordForm()

    return render(request, "account/create_password.html", {"form": form})


def login_view(request):

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():

            email = form.cleaned_data["email"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=email, password=password)

            if user is not None:
                login(request, user)
                return redirect("account:profile")

            else:
                form.add_error(None, "Invalid email or password")

    else:
        form = LoginForm()

    return render(request, "account/login.html", {"form": form})


@login_required
def profile(request):
    return render(request, "account/profile.html")


@login_required
def edit_profile(request):
    return HttpResponse("This is the edit profile page.")


def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            # Here you would typically send an email with a password reset link, but for simplicity, we'll just store the email in the session and redirect to the reset password page.
            request.session['reset_email'] = form.cleaned_data['email']
            return redirect("account:reset-password")

    else:
        form = ForgotPasswordForm()

    return render(request, "account/forgot_password.html", {"form": form})


def reset_password(request):
    # Get email from session
    email = request.session.get('reset_email')
    if not email:
        # If no email in session, redirect to forgot-password
        return redirect("account:forgot-password")

    if request.method == "POST":
        form = CreatePasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get("password1")
            try:
                user = Account.objects.get(email=email)
                user.set_password(password)
                user.save()
                
                # Clear email from session after reset
                del request.session['reset_email']
                
                return redirect("account:login")
            except Account.DoesNotExist:
                form.add_error(None, "No user found with this email.")
    else:
        form = CreatePasswordForm()

    return render(request, "account/create_password.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("account:login")