import re

from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, SetPasswordForm
from django.contrib.auth.password_validation import validate_password

from accounts.services import DuplicateAccountError, register_user

User = get_user_model()


class RegistrationForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "First name",
                "autocomplete": "given-name",
            }
        ),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Last name",
                "autocomplete": "family-name",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "field-input",
                "placeholder": "Email address",
                "autocomplete": "email",
            }
        )
    )
    username = forms.CharField(
        max_length=150,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Username",
                "autocomplete": "username",
            }
        ),
    )
    phone = forms.CharField(
        max_length=32,
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Phone number",
                "autocomplete": "tel",
            }
        ),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Password",
                "autocomplete": "new-password",
                "id": "id_password",
            }
        ),
    )
    password_confirm = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Confirm password",
                "autocomplete": "new-password",
                "id": "id_password_confirm",
            }
        ),
    )

    def clean_email(self):
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if len(username) < 3:
            raise forms.ValidationError("Username must be at least 3 characters.")
        if not re.fullmatch(r"[a-zA-Z0-9_.-]+", username):
            raise forms.ValidationError(
                "Username may contain letters, numbers, dots, hyphens, and underscores only."
            )
        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError("This username is already taken.")
        return username

    def clean_first_name(self):
        value = self.cleaned_data["first_name"].strip()
        if len(value) < 1:
            raise forms.ValidationError("Enter your first name.")
        return value

    def clean_last_name(self):
        value = self.cleaned_data["last_name"].strip()
        if len(value) < 1:
            raise forms.ValidationError("Enter your last name.")
        return value

    def clean_phone(self):
        phone = self.cleaned_data["phone"].strip()
        digits = re.sub(r"\D", "", phone)
        if len(digits) < 7:
            raise forms.ValidationError("Enter a valid phone number.")
        return phone

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Passwords do not match.")
        if password:
            validate_password(password)
        return cleaned

    def save(self):
        try:
            return register_user(
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                email=self.cleaned_data["email"],
                username=self.cleaned_data["username"],
                phone=self.cleaned_data["phone"],
                password=self.cleaned_data["password"],
            )
        except DuplicateAccountError as exc:
            raise forms.ValidationError(str(exc)) from exc


class EmailAuthenticationForm(AuthenticationForm):
    username = forms.CharField(
        label="Email or username",
        widget=forms.TextInput(
            attrs={
                "class": "field-input",
                "placeholder": "Email address or username",
                "autocomplete": "username",
                "autofocus": True,
            }
        ),
    )
    password = forms.CharField(
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "field-input",
                "placeholder": "Password",
                "autocomplete": "current-password",
                "id": "id_password",
            }
        ),
    )
    remember_me = forms.BooleanField(
        required=False,
        initial=False,
        widget=forms.CheckboxInput(attrs={"class": "checkbox-input"}),
    )

    error_messages = {
        "invalid_login": "Enter a valid email/username and password. Note that both fields may be case-sensitive.",
        "inactive": "This account is inactive.",
    }


class QuietPasswordResetForm(PasswordResetForm):
    """Always report success; do not reveal whether an email is registered."""

    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "field-input",
                "placeholder": "Email address",
                "autocomplete": "email",
            }
        )
    )


class StyledSetPasswordForm(SetPasswordForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "field-input"


class ProfileForm(forms.Form):
    first_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field-input", "autocomplete": "given-name"}),
    )
    last_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={"class": "field-input", "autocomplete": "family-name"}),
    )
    preferred_name = forms.CharField(
        max_length=150,
        required=False,
        widget=forms.TextInput(attrs={"class": "field-input", "autocomplete": "nickname"}),
    )
    phone = forms.CharField(
        max_length=32,
        required=False,
        widget=forms.TextInput(attrs={"class": "field-input", "autocomplete": "tel"}),
    )
    dark_mode = forms.BooleanField(required=False)

    def save(self, user):
        user.first_name = self.cleaned_data["first_name"].strip()
        user.last_name = self.cleaned_data["last_name"].strip()
        user.name = f"{user.first_name} {user.last_name}".strip()
        user.save(update_fields=["first_name", "last_name", "name"])
        profile = user.profile
        profile.preferred_name = self.cleaned_data["preferred_name"].strip()
        profile.phone = self.cleaned_data["phone"].strip()
        profile.save(update_fields=["preferred_name", "phone", "updated_at"])
        preferences = user.preferences
        preferences.dark_mode = self.cleaned_data["dark_mode"]
        preferences.save(update_fields=["dark_mode", "updated_at"])
        return user
