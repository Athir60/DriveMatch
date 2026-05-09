from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Avg
from django.conf import settings as django_settings
from datetime import timedelta

from .models import Booking, Contract, Payment, Rating, Invoice, Refund
from .forms import BookingForm, RatingForm
from drivers.models import DriverProfile, DriverRoute
from accounts.models import PassengerProfile



def _use_simulation():
    """Return True if no Moyasar key is configured."""
    return not bool(getattr(django_settings, 'MOYASAR_PUBLISHABLE_KEY', ''))


def _contract_number():
    year = timezone.now().year
    last = Contract.objects.order_by('-id').first()
    return f"CON-{year}-{str((last.id + 1) if last else 1).zfill(4)}"


def _invoice_number():
    year = timezone.now().year
    last = Invoice.objects.order_by('-id').first()
    return f"INV-{year}-{str((last.id + 1) if last else 1).zfill(4)}"


def _confirm_booking_payment(payment):
    """
    Called after a successful payment.
    Updates payment, confirms booking, creates Contract and Invoice.
    """
    with transaction.atomic():
        payment.status = Payment.PaymentStatus.PAID
        payment.paid_at = timezone.now()
        payment.save()

        booking = payment.booking
        booking.status = Booking.BookingStatus.CONFIRMED
        booking.start_date = timezone.now().date()
        booking.end_date = booking.start_date + timedelta(days=int(booking.subscription_months) * 30)
        booking.save()

        if not hasattr(booking, 'contract'):
            Contract.objects.create(
                booking=booking,
                contract_number=_contract_number(),
                status=Contract.ContractStatus.ACTIVE,
            )

        Invoice.objects.get_or_create(
            booking=booking,
            defaults={
                'invoice_number': _invoice_number(),
                'amount': payment.amount,
                'is_paid': True,
            }
        )



@login_required(login_url='/accounts/signin/')
def book_driver(request: HttpRequest, driver_route_id: int):
    """
    Step 1 of booking: Passenger selects route + duration.
    Creates Booking and Payment in PENDING state.
    Redirects to payment page — Contract and Invoice are created ONLY after payment.
    """
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Only passengers can make bookings.', 'alert-danger')
        return redirect('main:landing')

    driver_route = get_object_or_404(DriverRoute, id=driver_route_id, is_active=True)
    driver_profile = driver_route.driver
    max_months = int(driver_route.commitment_duration)

    if request.method == 'POST':
        form = BookingForm(request.POST, max_months=max_months)
        if form.is_valid():
            months = form.cleaned_data['subscription_months']
            total = driver_route.monthly_price * months
            try:
                with transaction.atomic():
                    booking = Booking.objects.create(
                        passenger=passenger_profile,
                        driver=driver_profile,
                        driver_route=driver_route,
                        subscription_months=months,
                        total_price=total,
                        status=Booking.BookingStatus.PAYMENT_PENDING,
                        agreed_to_terms=True,
                    )
                    payment = Payment.objects.create(
                        booking=booking,
                        amount=total,
                        status=Payment.PaymentStatus.PENDING,
                        payment_type=Payment.PaymentType.PASSENGER_BOOKING,
                    )
                return redirect('bookings:booking_payment', payment_id=payment.id)
            except Exception as e:
                messages.error(request, 'Could not create booking. Please try again.', 'alert-danger')
                print(f"[book_driver error] {e}")
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')
    else:
        form = BookingForm(max_months=max_months)

    return render(request, 'bookings/book_driver.html', {
        'form': form,
        'driver_route': driver_route,
        'driver_profile': driver_profile,
        'max_months': max_months,
    })



@login_required(login_url='/accounts/signin/')
def booking_payment(request: HttpRequest, payment_id: int):
    """
    Payment page for passenger booking.
    - Simulation mode (default): shows Confirm/Fail buttons.
    - Moyasar mode (when keys configured): shows Moyasar JS Payment Form.
    Raw card data is NEVER posted to Django.
    """
    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking

    try:
        if booking.passenger != request.user.passengerprofile:
            messages.error(request, 'Access denied.', 'alert-danger')
            return redirect('bookings:my_bookings')
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    if payment.status == Payment.PaymentStatus.PAID:
        messages.info(request, 'This payment has already been completed.', 'alert-info')
        return redirect('bookings:booking_detail', booking_id=booking.id)

    moyasar_key = getattr(django_settings, 'MOYASAR_PUBLISHABLE_KEY', '')
    callback_url = getattr(django_settings, 'MOYASAR_CALLBACK_URL', '')
    amount_halalas = int(payment.amount * 100)  # SAR → halalas for Moyasar

    return render(request, 'bookings/booking_payment.html', {
        'payment': payment,
        'booking': booking,
        'use_simulation': _use_simulation(),
        'moyasar_key': moyasar_key,
        'callback_url': callback_url,
        'amount_halalas': amount_halalas,
    })



@login_required(login_url='/accounts/signin/')
def simulate_booking_payment_success(request: HttpRequest, payment_id: int):
    """Simulation only: marks payment as paid and confirms booking."""
    if request.method != 'POST':
        return redirect('bookings:my_bookings')

    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking

    try:
        if booking.passenger != request.user.passengerprofile:
            return redirect('bookings:my_bookings')
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    if payment.status != Payment.PaymentStatus.PENDING:
        messages.warning(request, 'Payment already processed.', 'alert-warning')
        return redirect('bookings:booking_detail', booking_id=booking.id)

    payment.payment_reference = f"SIM-{payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
    payment.card_last4 = '0000'   # simulation only
    _confirm_booking_payment(payment)

    messages.success(request, 'Payment confirmed! Your booking is now active.', 'alert-success')
    return redirect('bookings:booking_detail', booking_id=booking.id)


@login_required(login_url='/accounts/signin/')
def simulate_booking_payment_failed(request: HttpRequest, payment_id: int):
    """Simulation only: marks payment as failed."""
    if request.method != 'POST':
        return redirect('bookings:my_bookings')

    payment = get_object_or_404(Payment, id=payment_id)
    booking = payment.booking

    try:
        if booking.passenger != request.user.passengerprofile:
            return redirect('bookings:my_bookings')
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    payment.status = Payment.PaymentStatus.FAILED
    payment.save()

    messages.error(request, 'Payment failed. Please try again.', 'alert-danger')
    return redirect('bookings:booking_payment', payment_id=payment.id)



def payment_callback(request: HttpRequest):
    """
    Handles return from Moyasar after payment.
    It supports:
    - local_payment_id from callback_url
    - Moyasar payment id from GET parameter: id
    - session fallback
    """

    moyasar_payment_id = request.GET.get('id', '')
    local_payment_id = request.GET.get('local_payment_id', '')
    status = request.GET.get('status', '')
    message_text = request.GET.get('message', 'Payment failed.')

    payment = None

    if local_payment_id:
        try:
            payment = Payment.objects.select_related('booking').get(id=int(local_payment_id))
        except (ValueError, Payment.DoesNotExist):
            payment = None

    if not payment and moyasar_payment_id:
        payment = Payment.objects.select_related('booking').filter(
            payment_reference=moyasar_payment_id
        ).first()

    if not payment:
        booking_id = request.session.get('pending_booking_id')
        if booking_id:
            booking = Booking.objects.filter(id=booking_id).first()
            if booking:
                payment = Payment.objects.filter(booking=booking).first()

    if not payment:
        messages.error(
            request,
            f'Could not verify payment. local_payment_id={local_payment_id}, moyasar_id={moyasar_payment_id}',
            'alert-danger'
        )
        return redirect('bookings:my_bookings')

    if status == 'paid':
        payment.payment_reference = moyasar_payment_id
        _confirm_booking_payment(payment)

        request.session.pop('pending_booking_id', None)

        messages.success(
            request,
            'Payment confirmed! Your booking is now active.',
            'alert-success'
        )
        return redirect('bookings:booking_detail', booking_id=payment.booking.id)

    payment.status = Payment.PaymentStatus.FAILED
    payment.payment_reference = moyasar_payment_id
    payment.save()

    messages.error(request, f'Payment failed: {message_text}', 'alert-danger')
    return redirect('bookings:booking_payment', payment_id=payment.id)

@login_required(login_url='/accounts/signin/')
def my_bookings(request: HttpRequest):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Only passengers can view bookings.', 'alert-danger')
        return redirect('main:landing')

    bookings_qs = Booking.objects.filter(passenger=passenger_profile).order_by('-created_at')
    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings_qs = bookings_qs.filter(status=status_filter)

    paginator = Paginator(bookings_qs, 10)
    bookings_page = paginator.get_page(request.GET.get('page', 1))

    visible_status_choices = [
        (val, label) for val, label in Booking.BookingStatus.choices
        if val != Booking.BookingStatus.CANCELLED_BY_DRIVER
    ]

    return render(request, 'bookings/my_bookings.html', {
        'bookings': bookings_page,
        'status_filter': status_filter,
        'visible_status_choices': visible_status_choices,
    })



@login_required(login_url='/accounts/signin/')
def booking_detail(request: HttpRequest, booking_id: int):
    try:
        passenger_profile = request.user.passengerprofile
        booking = get_object_or_404(Booking, id=booking_id, passenger=passenger_profile)
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Access denied.', 'alert-danger')
        return redirect('main:landing')

    try:
        contract = booking.contract
    except Contract.DoesNotExist:
        contract = None
    try:
        payment = booking.payment
    except Payment.DoesNotExist:
        payment = None

    has_rating = Rating.objects.filter(booking=booking).exists()

    return render(request, 'bookings/booking_detail.html', {
        'booking': booking,
        'contract': contract,
        'payment': payment,
        'has_rating': has_rating,
    })



@login_required(login_url='/accounts/signin/')
def contract_detail(request: HttpRequest, contract_id: int):
    contract = get_object_or_404(Contract, id=contract_id)
    booking = contract.booking
    is_passenger = (
        hasattr(request.user, 'passengerprofile') and
        booking.passenger == request.user.passengerprofile
    )
    is_driver = (
        hasattr(request.user, 'driverprofile') and
        booking.driver == request.user.driverprofile
    )
    if not (is_passenger or is_driver or request.user.is_staff):
        messages.error(request, 'Access denied.', 'alert-danger')
        return redirect('main:landing')
    try:
        payment = booking.payment
    except Payment.DoesNotExist:
        payment = None
    return render(request, 'bookings/contract_detail.html', {
        'contract': contract,
        'booking': booking,
        'payment': payment,
    })



@login_required(login_url='/accounts/signin/')
def rate_driver(request: HttpRequest, booking_id: int):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    booking = get_object_or_404(
        Booking, id=booking_id, passenger=passenger_profile,
        status=Booking.BookingStatus.COMPLETED
    )

    if Rating.objects.filter(booking=booking).exists():
        messages.warning(request, 'You have already rated this booking.', 'alert-warning')
        return redirect('bookings:my_bookings')

    form = RatingForm()
    if request.method == 'POST':
        form = RatingForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    rating = form.save(commit=False)
                    rating.booking = booking
                    rating.passenger = passenger_profile
                    rating.driver = booking.driver
                    rating.save()
                    avg = Rating.objects.filter(driver=booking.driver).aggregate(avg=Avg('stars'))
                    booking.driver.average_rating = avg['avg'] or 0
                    booking.driver.save()
                messages.success(request, 'Rating submitted. Thank you!', 'alert-success')
                return redirect('bookings:my_bookings')
            except Exception as e:
                messages.error(request, 'Could not submit rating.', 'alert-danger')
                print(e)
        else:
            messages.error(request, 'Please select a star rating.', 'alert-danger')

    return render(request, 'bookings/rate_driver.html', {'form': form, 'booking': booking})



@login_required(login_url='/accounts/signin/')
def my_invoices(request: HttpRequest):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    invoices = Invoice.objects.filter(
        booking__passenger=passenger_profile
    ).order_by('-issued_date')

    paginator = Paginator(invoices, 10)
    invoices_page = paginator.get_page(request.GET.get('page', 1))
    return render(request, 'bookings/my_invoices.html', {'invoices': invoices_page})
