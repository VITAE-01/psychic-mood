from django.shortcuts import render, redirect
from django.http import HttpResponse
from .models import Account
from .forms import RegisterForm
from .forms import CreatePasswordForm
from .forms import LoginForm
from .forms import ForgotPasswordForm
from django.contrib.auth import get_user_model, authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import never_cache
from .utils import write_active_user_to_csv


User = get_user_model()


# Create your views here.
# /account -> index view will be called when the user visits the account page.
def index(request):
    return render(request, "account/index.html", { 'show_signup_button': not request.user.is_authenticated })

def signup(request):

    if request.method == "POST":
        form = RegisterForm(request.POST)

        if form.is_valid():
            user = form.save(commit=False)

            user.set_unusable_password()   # important
            user.is_active = False         # until email verification
            user.save()

            request.session["registration_username"] = user.username

            return redirect("account:create-password")

    else:
        form = RegisterForm()

    return render(request, "account/register.html", {"form": form})


# def verify_email(request):
#     return HttpResponse("This is the email verification page.")


def create_password(request):
    # Get username from session
    username = request.session.get("registration_username")

    # if no username in session, redirect to signup page
    if not username:
        return redirect("account:register")
    
    try:
        user = User.objects.get(username=username, is_active=False)
        if user.is_active:
            # If user is already active, redirect to login page
            return redirect("account:login")
    except User.DoesNotExist:
        # If no user found with the username, redirect to signup page
        return redirect("account:register")
    
    if request.method == "POST":
        form = CreatePasswordForm(request.POST)

        if form.is_valid():

            user = User.objects.get(username=username)
            user.set_password(form.cleaned_data["password1"])
            user.is_active = True
            user.save()

            # --- Log user to CSV only after password is set ---
            write_active_user_to_csv(user)
            # --- End of CSV logging ---

            # Clear the username from session after successful password creation
            request.session.pop("registration_username", None)

            return redirect("account:login")

    else:
        form = CreatePasswordForm()

    return render(request, "account/create_password.html", {"form": form})


def login_view(request):

    if request.method == "POST":
        form = LoginForm(request.POST)

        if form.is_valid():

            username = form.cleaned_data["username"]
            password = form.cleaned_data["password"]

            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                return redirect("dashboard:index")

            else:
                form.add_error(None, "Invalid username or password")
                form.cleaned_data["password"] = ""  # Clear password field

    else:
        form = LoginForm()

    return render(request, "account/login.html", {"form": form})


@login_required
@never_cache
def profile(request):
    return render(request, "account/profile.html", { 'show_logout_button': True })


@login_required
@never_cache
def edit_profile(request):
    return HttpResponse("This is the edit profile page.")


def forgot_password(request):
    if request.method == "POST":
        form = ForgotPasswordForm(request.POST)

        if form.is_valid():
            # Here you would typically send an email with a password reset link, but for simplicity, we'll just store the username in the session and redirect to the reset password page.
            request.session['reset_username'] = form.cleaned_data['username']
            return redirect("account:reset-password")

    else:
        form = ForgotPasswordForm()

    return render(request, "account/forgot_password.html", {"form": form})


def reset_password(request):
    # Get username from session
    username = request.session.get('reset_username')
    if not username:
        # If no username in session, redirect to forgot-password
        return redirect("account:forgot-password")

    if request.method == "POST":
        form = CreatePasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data.get("password1")
            try:
                user = Account.objects.get(username=username)
                user.set_password(password)
                user.save()
                
                # Clear username from session after reset
                del request.session['reset_username']
                
                return redirect("account:login")
            except Exception as e:
                form.add_error(None, "No user found with this username.")
                return render(request, "account/create_password.html", {"form": form})
    else:
        form = CreatePasswordForm()

    return render(request, "account/create_password.html", {"form": form})


def logout_view(request):
    logout(request)
    return redirect("landing-page")