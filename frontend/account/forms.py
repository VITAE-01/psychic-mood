import email

from django import forms
from .models import Account
from datetime import date
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

GENDER_CHOICES = [
    ("", "Select"), 
    ('male', 'Male'),
    ('female', 'Female'),
    ('other', 'Prefer not to say'),
]

AGE_CHOICES = [
    ("", "Select"),
    ('18-24', '18-24'),
    ('25-34', '25-34'),
    ('35-44', '35-44'),
    ('45-54', '45-54'),
    ('55+', '55+'),
]


class RegisterForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = [
            "username",
            "age_range",
            "gender",
            "height",
            "weight",
        ]

        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your username"}),
            "age_range": forms.Select(attrs={"class": "form-select"}, choices=AGE_CHOICES),
            "gender": forms.Select(attrs={"class": "form-select"}, choices=GENDER_CHOICES),
            "height": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g 160", "min": 0}),
            "weight": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g 55", "min": 0}),
        }

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if Account.objects.filter(username=username).exists():
            raise forms.ValidationError("Sorry! Username is already taken. Please choose a different username.")
        return username

    def clean_height(self):
        height = self.cleaned_data.get("height")
        if height is None:
            return height
        if height > 300:
            raise forms.ValidationError("Height cannot be greater than 300 cm.")
        if height is not None and height < 0:
            raise forms.ValidationError("Height cannot be negative.")
        return height

    def clean_weight(self):
        weight = self.cleaned_data.get("weight")
        if weight is None:
            return weight
        if weight > 500:
            raise forms.ValidationError("Weight cannot be greater than 500 kg.")
        if weight is not None and weight < 0:
            raise forms.ValidationError("Weight cannot be negative.")
        return weight

class CreatePasswordForm(forms.Form):

    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Create a password"}),
        label="Password"
    )

    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm your password"}),
        label="Confirm Password"
    )

    def clean(self):
        cleaned_data = super().clean()

        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")

        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("Passwords do not match")

            validate_password(password1)

        return cleaned_data
    

class LoginForm(forms.Form):
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput)
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter your password"}))


class ForgotPasswordForm(forms.Form):
    username = forms.CharField()
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your username"}))
    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not Account.objects.filter(username=username).exists():
            raise forms.ValidationError("Sorry! Username not found. Please try again.")
        return username