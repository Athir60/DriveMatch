from django.db import models
from django.contrib.auth.models import User


class PassengerProfile(models.Model):
    """
    One passenger profile per user.
    Linked with OneToOneField just like GamesHaven's Profile model.
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    city = models.CharField(max_length=100, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Passenger: {self.user.get_full_name()} ({self.user.username})"


class EmailOTP(models.Model):
    PURPOSE_CHOICES = [
        ('registration', 'Registration'),
        ('email_change', 'Email Change'),
        ('driver_registration', 'Driver Registration'),
    ]

    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=30, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.email} - {self.purpose} - {self.otp_code}"