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

max_dob = date.today().replace(year=date.today().year - 18)


class RegisterForm(forms.ModelForm):

    class Meta:
        model = Account
        fields = [
            "first_name",
            "last_name",
            "email",
            "date_of_birth",
            "gender",
            "height",
            "weight",
        ]

        widgets = {
        "first_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your first name"}),
        "last_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter your last name"}),
        "email": forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"}),
        "date_of_birth": forms.DateInput(attrs={"class": "form-control", "type": "date", "max": max_dob.strftime("%Y-%m-%d")}),
        "gender": forms.Select(attrs={"class": "form-select"}, choices=GENDER_CHOICES),
        "height": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g 160", "min": 0}),
        "weight": forms.NumberInput(attrs={"class": "form-control", "placeholder": "e.g 55", "min": 0}),
    }

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get("date_of_birth")
        if dob is None:
            raise forms.ValidationError("This field is required.")
        
        if dob > date.today():
            raise forms.ValidationError("Date of birth cannot be in the future.")
        
        today = date.today()
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
        if age < 18:
            raise forms.ValidationError("You must be at least 18 years old to register.")
        return dob
                
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
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your email"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Enter your password"}))


class ForgotPasswordForm(forms.Form):
    email = forms.EmailField()
    email = forms.EmailField(widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Enter your registered email"}))
    def clean_email(self):
        email = self.cleaned_data.get("email")
        if not Account.objects.filter(email=email).exists():
            raise forms.ValidationError("Sorry! Email address not found. Please try again.")
        return email