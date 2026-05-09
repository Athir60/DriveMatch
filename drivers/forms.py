from django import forms
from django.contrib.auth.models import User

from .models import (
    DriverProfile, Vehicle, Route, DriverRoute,
    DriverSubscription, SubscriptionPlan, DriverBankAccount
)
from accounts.forms import validate_strong_password, validate_full_name, normalize_saudi_phone

TIME_CHOICES = [
    ('', 'Select time'),
    ('00:00', '00:00'), ('01:00', '01:00'), ('02:00', '02:00'),
    ('03:00', '03:00'), ('04:00', '04:00'), ('05:00', '05:00'),
    ('06:00', '06:00'), ('07:00', '07:00'), ('08:00', '08:00'),
    ('09:00', '09:00'), ('10:00', '10:00'), ('11:00', '11:00'),
    ('12:00', '12:00'), ('13:00', '13:00'), ('14:00', '14:00'),
    ('15:00', '15:00'), ('16:00', '16:00'), ('17:00', '17:00'),
    ('18:00', '18:00'), ('19:00', '19:00'), ('20:00', '20:00'),
    ('21:00', '21:00'), ('22:00', '22:00'), ('23:00', '23:00'),
]


class DriverAgreementForm(forms.Form):
    agree = forms.BooleanField(
        error_messages={'required': 'You must agree to the driver terms and conditions.'}
    )


class DriverPersonalInfoForm(forms.Form):
    full_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your full name (e.g. Ahmed Ali)'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Enter your email address'})
    )
    phone_number = forms.CharField(
        max_length=20,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '5xxxxxxxx'})
    )
    national_id = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your ID or Iqama number'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Create a password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm your password'})
    )

    profile_photo = forms.ImageField(
        required=False,
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-sm', 
            'accept': 'image/*',
            'style': 'font-size: 11px;' 
        })
    )

    id_front = forms.ImageField(
        required=True,
        error_messages={'required': 'ID / Iqama (Front) photo is required.'},
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-sm', 
            'accept': 'image/*', 
            'style': 'font-size: 11px;'
        })
    )
    id_back = forms.ImageField(
        required=True,
        error_messages={'required': 'ID / Iqama (Back) photo is required.'},
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-sm', 
            'accept': 'image/*', 
            'style': 'font-size: 11px;'
        })
    )
    driver_license = forms.ImageField(
        required=True,
        error_messages={'required': 'Driver License photo is required.'},
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control form-control-sm', 
            'accept': 'image/*', 
            'style': 'font-size: 11px;'
        })
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
        if DriverProfile.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError("This phone number is already registered.")
        from accounts.models import PassengerProfile
        if PassengerProfile.objects.filter(phone_number=phone).exists():
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



class VehicleForm(forms.ModelForm):

    def clean_year(self):
        year = self.cleaned_data.get('year')
        if year and (year < 2000 or year > 2026):
            raise forms.ValidationError("Please enter a valid car year between 2000 and 2026.")
        return year

    def clean_license_plate(self):
        plate = self.cleaned_data.get('license_plate', '').strip().upper()
        if not plate:
            raise forms.ValidationError("License plate is required.")
        qs = Vehicle.objects.filter(license_plate__iexact=plate)
        if self.instance and self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise forms.ValidationError("This license plate is already registered.")
        return plate

    class Meta:
        model = Vehicle
        fields = ['brand', 'model', 'year', 'color', 'license_plate', 'car_type', 'car_photo']
        widgets = {
            'brand':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Toyota'}),
            'model':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Camry'}),
            'year':          forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 2022', 'min': '2000', 'max': '2026'}),
            'color':         forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. White'}),
            'license_plate': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. ABC 1234'}),
            'car_type':      forms.Select(attrs={'class': 'form-select'}),
            'car_photo':     forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }



class DriverRouteForm(forms.ModelForm):
    DAYS_CHOICES = [
        ('Sun', 'Sunday'), ('Mon', 'Monday'), ('Tue', 'Tuesday'),
        ('Wed', 'Wednesday'), ('Thu', 'Thursday'), ('Fri', 'Friday'), ('Sat', 'Saturday'),
    ]
    days = forms.MultipleChoiceField(
        choices=DAYS_CHOICES,
        widget=forms.CheckboxSelectMultiple(),
        required=True,
        error_messages={'required': 'Please select at least one available day.'}
    )

    class Meta:
        model = DriverRoute
        fields = ['route', 'start_time', 'end_time', 'monthly_price', 'commitment_duration']
        widgets = {
            'route':               forms.Select(attrs={'class': 'form-select'}),
            'start_time':          forms.Select(choices=TIME_CHOICES, attrs={'class': 'form-select'}),
            'end_time':            forms.Select(choices=TIME_CHOICES, attrs={'class': 'form-select'}),
            'monthly_price':       forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 800', 'min': '1'}),
            'commitment_duration': forms.Select(attrs={'class': 'form-select'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_time')
        end   = cleaned_data.get('end_time')
        if start and end and end <= start:
            raise forms.ValidationError("End time must be after start time.")
        price = cleaned_data.get('monthly_price')
        if price is not None and price < 1:
            raise forms.ValidationError("Monthly price must be at least 1 SAR.")
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.available_days:
            self.fields['days'].initial = self.instance.get_days_list()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.available_days = ','.join(self.cleaned_data['days'])
        if commit:
            instance.save()
        return instance



class DriverProfileUpdateForm(forms.ModelForm):
    """Allows driver to update personal info, profile photo, and documents."""
    class Meta:
        model = DriverProfile
        fields = [
            'profile_photo',
            'phone_number', 'national_id', 'bio',
            'id_front', 'id_back', 'driver_license',
        ]
        widgets = {
            'profile_photo':  forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'phone_number':   forms.TextInput(attrs={'class': 'form-control'}),
            'national_id':    forms.TextInput(attrs={'class': 'form-control'}),
            'bio':            forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'id_front':       forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'id_back':        forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
            'driver_license': forms.ClearableFileInput(attrs={'class': 'form-control', 'accept': 'image/*'}),
        }



class DriverBankAccountForm(forms.ModelForm):

    def clean_iban(self):
        iban = self.cleaned_data.get('iban', '').strip().upper().replace(' ', '')
        if not iban:
            raise forms.ValidationError("IBAN is required.")
        if not iban.startswith('SA'):
            raise forms.ValidationError("Saudi bank IBAN must start with 'SA'.")
        if len(iban) != 24:
            raise forms.ValidationError("Saudi IBAN must be exactly 24 characters (e.g. SA0380000000608010167519).")
        return iban

    class Meta:
        model = DriverBankAccount
        fields = ['bank_name', 'iban', 'account_holder_name']
        widgets = {
            'bank_name':           forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Al Rajhi Bank'}),
            'iban':                forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'SA0380000000608010167519'}),
            'account_holder_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full name on bank account'}),
        }