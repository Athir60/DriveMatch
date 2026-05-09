from django import forms
from django.contrib.auth.models import User
from .models import PassengerProfile

def validate_strong_password(password):
    """
    Shared password validator used in all password forms.
    Rules: 8+ chars, one uppercase, one digit.
    Valid example: Ahmed123
    """
    if len(password) < 8:
        raise forms.ValidationError("Password must be at least 8 characters.")
    if not any(ch.isupper() for ch in password):
        raise forms.ValidationError("Password must contain at least one uppercase letter.")
    if not any(ch.isdigit() for ch in password):
        raise forms.ValidationError("Password must contain at least one number.")


def validate_full_name(name):
    """
    Full name must have at least two words, each at least 2 characters.
    Valid: Ahmed Ali, Mohammed Abdullah
    Invalid: Ahmed, x y
    """
    parts = name.strip().split()
    if len(parts) < 2 or any(len(p) < 2 for p in parts):
        raise forms.ValidationError(
            "Please enter your full name with at least first and last name "
            "(e.g. Ahmed Ali)."
        )


def normalize_saudi_phone(phone):
    """
    Normalize Saudi mobile numbers.
    Accepts: 591817302 or 0591817302
    Returns: 591817302  (9 digits, starts with 5)
    Raises ValidationError if invalid.
    """
    phone = phone.strip().replace(' ', '').replace('-', '')
    if phone.startswith('0'):
        phone = phone[1:]
    if not phone.isdigit():
        raise forms.ValidationError("Enter a valid Saudi mobile number, for example 591817302.")
    if len(phone) != 9:
        raise forms.ValidationError("Enter a valid Saudi mobile number, for example 591817302.")
    if not phone.startswith('5'):
        raise forms.ValidationError("Enter a valid Saudi mobile number, for example 591817302.")
    return phone



class PassengerRegistrationForm(forms.Form):
    """
    Passenger registration form.
    - Email saved lowercase (prevents case-mismatch login).
    - Phone normalized to 9-digit Saudi format.
    - Password enforced: 8+ chars, uppercase, digit.
    - Full name: 2+ words, 2+ chars each.
    """
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name (e.g. Ahmed Ali)',
        })
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email address',
        })
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '5xxxxxxxx',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password',
        })
    )
    agree_terms = forms.BooleanField(
        error_messages={'required': 'You must agree to the Terms of Service and Privacy Policy.'}
    )

    def clean_full_name(self):
        name = self.cleaned_data.get('full_name', '')
        validate_full_name(name)
        return name.strip()

    def clean_email(self):
        email = self.cleaned_data.get('email', '').strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("This email is already registered. Please use another email.")
        return email

    def clean_phone_number(self):
        raw = self.cleaned_data.get('phone_number', '')
        phone = normalize_saudi_phone(raw)   
       
        if PassengerProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        from drivers.models import DriverProfile
        if DriverProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return phone

    def clean_password(self):
        password = self.cleaned_data.get('password', '')
        validate_strong_password(password)
        return password

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        confirm = cleaned_data.get('confirm_password')
        if pw and confirm and pw != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data




class PassengerProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = PassengerProfile
        fields = ['phone_number', 'city']
        widgets = {
            'phone_number': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
        }



class SignInForm(forms.Form):
    """
    Sign-in form using email address.
    The view does case-insensitive lookup then calls authenticate()
    with the stored username to fix case-mismatch issues.
    """
    email = forms.EmailField(
        label='Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email address',
            'autocomplete': 'email',
        })
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        })
    )

class ForgotPasswordForm(forms.Form):
    """Step 1: user submits their registered email."""
    email = forms.EmailField(
        label='Registered Email Address',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your registered email address',
        })
    )

    def clean_email(self):
        return self.cleaned_data['email'].strip().lower()


class VerifyResetCodeForm(forms.Form):
    """Step 2: user enters the 6-digit OTP displayed on screen."""
    code = forms.CharField(
        max_length=6,
        min_length=6,
        label='Verification Code',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the 6-digit code',
            'autocomplete': 'off',
            'inputmode': 'numeric',
            'style': 'letter-spacing:6px; font-size:20px; text-align:center;',
        })
    )

    def clean_code(self):
        code = self.cleaned_data.get('code', '').strip()
        if not code.isdigit():
            raise forms.ValidationError("The code must contain digits only.")
        return code


class ResetPasswordForm(forms.Form):
    """Step 3: user sets a new password — same rules as registration."""
    new_password = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password',
        })
    )
    confirm_password = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password',
        })
    )

    def clean_new_password(self):
        password = self.cleaned_data.get('new_password', '')
        validate_strong_password(password)   # same rules everywhere
        return password

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('new_password')
        confirm = cleaned_data.get('confirm_password')
        if pw and confirm and pw != confirm:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data
