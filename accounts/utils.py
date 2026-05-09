import random
from django.utils import timezone
from datetime import timedelta
from django.core.mail import send_mail

from .models import EmailOTP


def generate_otp():
    return str(random.randint(100000, 999999))


def send_otp_email(email, code):
    send_mail(
        subject='DriveMatch — Email Verification Code',
        message=f'Your verification code is: {code}',
        from_email=None,  # uses DEFAULT_FROM_EMAIL
        recipient_list=[email],
        fail_silently=False,
    )


def create_otp(email, purpose):
    code = generate_otp()

    otp = EmailOTP.objects.create(
        email=email,
        otp_code=code,
        purpose=purpose,
        expires_at=timezone.now() + timedelta(minutes=10)
    )

    send_otp_email(email, code)

    return otp


def verify_otp(email, code, purpose):
    try:
        otp = EmailOTP.objects.filter(
            email=email,
            otp_code=code,
            purpose=purpose,
            is_used=False
        ).latest('created_at')

        if otp.expires_at < timezone.now():
            return False

        otp.is_used = True
        otp.save()

        return True

    except EmailOTP.DoesNotExist:
        return False