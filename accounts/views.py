import random
from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib.auth.models import User, Group
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError

from .models import PassengerProfile
from .forms import (
    PassengerRegistrationForm, PassengerProfileUpdateForm,
    SignInForm, ForgotPasswordForm, VerifyResetCodeForm, ResetPasswordForm
)




from .utils import create_otp  # 🔥 أضف هذا فوق مع الـ imports


def passenger_register(request: HttpRequest):
    """Register with OTP verification"""
    form = PassengerRegistrationForm()

    if request.method == 'POST':
        form = PassengerRegistrationForm(request.POST)
        if form.is_valid():

            request.session['pending_registration'] = {
                'email': form.cleaned_data['email'],
                'password': form.cleaned_data['password'],
                'full_name': form.cleaned_data['full_name'],
                'phone_number': form.cleaned_data['phone_number'],
            }

            create_otp(
                email=form.cleaned_data['email'],
                purpose='registration'
            )

            messages.success(
                request,
                'Verification code sent to your email.',
                'alert-success'
            )

            return redirect('accounts:verify_registration_otp')

    return render(request, 'accounts/passenger_register.html', {'form': form})


def sign_in(request: HttpRequest):
    """
    Sign in using email address (case-insensitive).

    Why the previous version failed:
    - authenticate(username=raw_email) does an exact-match on the username field.
    - If user registered with 'ahmed@gmail.com' but typed 'Ahmed@gmail.com',
      authenticate() returns None because the match is case-sensitive.

    Fix:
    1. Normalize the submitted email to lowercase.
    2. Look up the User by email__iexact (case-insensitive).
    3. Call authenticate() using the stored user.username (which is always lowercase).
    """
    form = SignInForm()

    if request.method == 'POST':
        form = SignInForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email'].strip().lower()
            password = form.cleaned_data['password']

            user_obj = User.objects.filter(email__iexact=email).first()
            if user_obj is None:
                user_obj = User.objects.filter(username__iexact=email).first()

            if user_obj:
                user = authenticate(request, username=user_obj.username, password=password)
            else:
                user = None

            if user is not None:
                login(request, user)
                messages.success(
                    request,
                    f'Welcome back, {user.get_full_name() or user.username}!',
                    'alert-success'
                )
                if user.is_superuser or user.is_staff:
                    return redirect('/admin/')
                elif user.groups.filter(name='Driver').exists():
                    return redirect('drivers:driver_dashboard')
                else:
                    next_url = request.GET.get('next', '')
                    if next_url:
                        return redirect(next_url)
                    return redirect('main:passenger_home')
            else:
                messages.error(
                    request,
                    'Incorrect email or password. Please try again.',
                    'alert-danger'
                )

    return render(request, 'accounts/signin.html', {'form': form})



def sign_out(request: HttpRequest):
    logout(request)
    messages.success(request, 'You have been signed out.', 'alert-warning')
    return redirect('main:landing')



def forgot_password(request: HttpRequest):
    """
    Step 1 of password reset.
    User enters registered email.
    A simulated 6-digit OTP is generated and shown (no real email sent).
    """
    form = ForgotPasswordForm()

    if request.method == 'POST':
        form = ForgotPasswordForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']   # already lowercase from clean_email()

            user_obj = User.objects.filter(email__iexact=email).first()
            if user_obj is None:
                user_obj = User.objects.filter(username__iexact=email).first()

            if user_obj is None:
                messages.error(
                    request,
                    'No account found with this email address.',
                    'alert-danger'
                )
            else:
                code = str(random.randint(100000, 999999))

                request.session['reset_email'] = user_obj.email
                request.session['reset_code'] = code
                request.session['reset_verified'] = False

                messages.success(
                    request,
                    f'Verification code for testing: {code}',
                    'alert-success'
                )
                return redirect('accounts:verify_reset_code')

    return render(request, 'accounts/forgot_password.html', {'form': form})



def verify_reset_code(request: HttpRequest):
    """
    Step 2 of password reset.
    User enters the 6-digit OTP shown in the previous step message.
    """
    if not request.session.get('reset_code'):
        messages.error(request, 'Please start from the forgot password page.', 'alert-danger')
        return redirect('accounts:forgot_password')

    form = VerifyResetCodeForm()

    if request.method == 'POST':
        form = VerifyResetCodeForm(request.POST)
        if form.is_valid():
            entered_code = form.cleaned_data['code']
            stored_code = request.session.get('reset_code', '')

            if entered_code == stored_code:
                request.session['reset_verified'] = True
                messages.success(request, 'Code verified. Please set your new password.', 'alert-success')
                return redirect('accounts:reset_password')
            else:
                messages.error(request, 'Invalid verification code. Please try again.', 'alert-danger')

    reset_email = request.session.get('reset_email', '')
    return render(request, 'accounts/verify_reset_code.html', {
        'form': form,
        'reset_email': reset_email,
    })



def reset_password(request: HttpRequest):
    """
    Step 3 of password reset.
    User enters new password.
    Uses set_password() so Django hashes it correctly.
    """
    if not request.session.get('reset_verified'):
        messages.error(request, 'Please verify your code first.', 'alert-danger')
        return redirect('accounts:forgot_password')

    reset_email = request.session.get('reset_email', '')
    form = ResetPasswordForm()

    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            new_password = form.cleaned_data['new_password']

            user_obj = User.objects.filter(email__iexact=reset_email).first()
            if user_obj is None:
                user_obj = User.objects.filter(username__iexact=reset_email).first()

            if user_obj:
                user_obj.set_password(new_password)
                user_obj.save()

                for key in ['reset_email', 'reset_code', 'reset_verified']:
                    request.session.pop(key, None)

                messages.success(
                    request,
                    'Password reset successfully. Please sign in with your new password.',
                    'alert-success'
                )
                return redirect('accounts:sign_in')
            else:
                messages.error(request, 'Could not find the account. Please try again.', 'alert-danger')
                return redirect('accounts:forgot_password')

    return render(request, 'accounts/reset_password.html', {
        'form': form,
        'reset_email': reset_email,
    })



def forgot_username(request: HttpRequest):
    return render(request, 'accounts/forgot_username.html')



@login_required(login_url='/accounts/signin/')
def passenger_profile(request: HttpRequest):
    try:
        profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Passenger profile not found.', 'alert-danger')
        return redirect('main:landing')

    form = PassengerProfileUpdateForm(instance=profile)

    if request.method == 'POST':
        form = PassengerProfileUpdateForm(request.POST, instance=profile)
        if form.is_valid():
            try:
                with transaction.atomic():
                    full_name = request.POST.get('full_name', '').strip()
                    if full_name:
                        name_parts = full_name.split(' ', 1)
                        request.user.first_name = name_parts[0]
                        request.user.last_name = name_parts[1] if len(name_parts) > 1 else ''
                        request.user.save()
                    form.save()
                messages.success(request, 'Profile updated successfully.', 'alert-success')
                return redirect('accounts:passenger_profile')
            except Exception as e:
                messages.error(request, 'Could not update profile.', 'alert-danger')
                print(f"[Profile Update Error] {e}")

    return render(request, 'accounts/passenger_profile.html', {'form': form, 'profile': profile})



def _send_otp_email(new_email, otp_code):
    """
    Attempt to send OTP via Django email backend.
    In development (no SMTP configured), prints to terminal instead.
    """
    from django.core.mail import send_mail
    from django.conf import settings
    try:
        send_mail(
            subject='DriveMatch — Email Verification Code',
            message=(
                f'Your verification code is: {otp_code}\n\n'
                f'This code expires in 10 minutes.\n'
                f'If you did not request this, please ignore this email.'
            ),
            from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@drivematch.com'),
            recipient_list=[new_email],
            fail_silently=False,
        )
        return True, None
    except Exception as e:
        print(f"\n[DEV] OTP for {new_email}: {otp_code}\n")
        return False, str(e)


@login_required(login_url='/accounts/signin/')
def request_email_change(request: HttpRequest):
    """
    Step 1: User requests to change email.
    Generates OTP, stores in session, sends to new email.
    """
    if request.method != 'POST':
        return redirect('accounts:passenger_profile')

    new_email = request.POST.get('new_email', '').strip().lower()

    if not new_email:
        messages.error(request, 'Please enter a new email address.', 'alert-danger')
        return redirect('accounts:passenger_profile')

    from django.core.validators import validate_email
    from django.core.exceptions import ValidationError
    try:
        validate_email(new_email)
    except ValidationError:
        messages.error(request, 'Please enter a valid email address.', 'alert-danger')
        return redirect('accounts:passenger_profile')

    if User.objects.filter(email__iexact=new_email).exclude(pk=request.user.pk).exists():
        messages.error(
            request,
            'This email address is already registered. Please use a different email.',
            'alert-danger'
        )
        return redirect('accounts:passenger_profile')

    import random
    otp = str(random.randint(100000, 999999))
    request.session['email_change_otp'] = otp
    request.session['email_change_target'] = new_email

    sent, error = _send_otp_email(new_email, otp)

    if sent:
        messages.success(
            request,
            f'A verification code has been sent to {new_email}.',
            'alert-success'
        )
    else:
        messages.success(
            request,
            f'[Development Mode] Email could not be sent (no SMTP configured). '
            f'Your OTP code is: {otp}',
            'alert-warning'
        )

    return redirect('accounts:verify_email_otp')


@login_required(login_url='/accounts/signin/')
def verify_email_otp(request: HttpRequest):
    """
    Step 2: User enters the OTP to verify new email.
    On success, updates User.email, User.username, and marks is_email_verified.
    """
    stored_otp = request.session.get('email_change_otp')
    new_email = request.session.get('email_change_target')

    if not stored_otp or not new_email:
        messages.error(request, 'No email change in progress. Please start again.', 'alert-danger')
        return redirect('accounts:passenger_profile')

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')

        if action == 'resend':
            import random
            otp = str(random.randint(100000, 999999))
            request.session['email_change_otp'] = otp
            sent, _ = _send_otp_email(new_email, otp)
            if sent:
                messages.success(request, f'A new code has been sent to {new_email}.', 'alert-success')
            else:
                messages.success(
                    request,
                    f'[Development Mode] New OTP: {otp}',
                    'alert-warning'
                )
            return redirect('accounts:verify_email_otp')

        entered_code = request.POST.get('otp_code', '').strip()
        if entered_code == stored_otp:
            try:
                with transaction.atomic():
                    request.user.email = new_email
                    request.user.username = new_email   # email is used as username
                    request.user.save()
                    try:
                        request.user.passengerprofile.is_email_verified = True
                        request.user.passengerprofile.save()
                    except PassengerProfile.DoesNotExist:
                        pass
                for key in ['email_change_otp', 'email_change_target']:
                    request.session.pop(key, None)
                messages.success(
                    request,
                    f'Email updated successfully to {new_email}.',
                    'alert-success'
                )
                return redirect('accounts:passenger_profile')
            except Exception as e:
                messages.error(request, 'Could not update email. Please try again.', 'alert-danger')
                print(f"[Email Change Error] {e}")
        else:
            messages.error(request, 'Invalid verification code. Please try again.', 'alert-danger')

    return render(request, 'accounts/verify_email_otp.html', {
        'new_email': new_email,
    })

from .utils import verify_otp


def verify_registration_otp(request: HttpRequest):
    data = request.session.get('pending_registration')

    if not data:
        messages.error(request, 'Session expired. Please register again.', 'alert-danger')
        return redirect('accounts:passenger_register')

    if request.method == 'POST':
        action = request.POST.get('action', 'verify')

        if action == 'resend':
            create_otp(
                email=data['email'],
                purpose='registration'
            )

            messages.success(request, 'A new verification code has been sent.', 'alert-success')
            return redirect('accounts:verify_registration_otp')

        code = request.POST.get('otp_code', '').strip()

        if verify_otp(data['email'], code, 'registration'):
            try:
                with transaction.atomic():

                    full_name = data['full_name'].strip()
                    name_parts = full_name.split(' ', 1)
                    first_name = name_parts[0]
                    last_name = name_parts[1] if len(name_parts) > 1 else ''

                    new_user = User.objects.create_user(
                        username=data['email'],
                        email=data['email'],
                        password=data['password'],
                        first_name=first_name,
                        last_name=last_name,
                    )

                    PassengerProfile.objects.create(
                        user=new_user,
                        phone_number=data['phone_number'],
                        is_phone_verified=True,
                        is_email_verified=True,
                    )

                    passenger_group, _ = Group.objects.get_or_create(name='Passenger')
                    new_user.groups.add(passenger_group)

                request.session.pop('pending_registration', None)

                messages.success(request, 'Account verified and created successfully!', 'alert-success')
                return redirect('accounts:sign_in')

            except Exception as e:
                messages.error(request, 'Error creating account.', 'alert-danger')
                print(f"[OTP Create Error] {e}")

        else:
            messages.error(request, 'Invalid or expired code.', 'alert-danger')

    return render(request, 'accounts/verify_email_otp.html', {
    'new_email': data['email']
})
