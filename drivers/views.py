from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib.auth.models import User, Group
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Avg, Sum

from .models import (
    DriverProfile, Vehicle, Route, DriverRoute,
    SubscriptionPlan, DriverSubscription,
    FavoriteDriver, DriverCancellationRequest, DriverBankAccount,
    DriverSubscriptionPayment
)
from .forms import (
    DriverAgreementForm, DriverPersonalInfoForm,
    VehicleForm, DriverRouteForm, DriverProfileUpdateForm, DriverBankAccountForm
)
from accounts.models import PassengerProfile



def driver_register_step1(request: HttpRequest):
    form = DriverAgreementForm()
    if request.method == 'POST':
        form = DriverAgreementForm(request.POST)
        if form.is_valid():
            request.session['driver_reg_step1'] = True
            return redirect('drivers:driver_register_step2')
    return render(request, 'drivers/register_step1.html', {'form': form, 'current_step': 1})



def driver_register_step2(request: HttpRequest):
    if not request.session.get('driver_reg_step1'):
        return redirect('drivers:driver_register_step1')

    form = DriverPersonalInfoForm()

    if request.method == 'POST':
        form = DriverPersonalInfoForm(request.POST, request.FILES)

        if form.is_valid():
            try:
                with transaction.atomic():
                    email = form.cleaned_data['email']
                    full_name = form.cleaned_data['full_name'].strip()
                    parts = full_name.split(' ', 1)
                    new_user = User.objects.create_user(
                        username=email,
                        email=email,
                        password=form.cleaned_data['password'],
                        first_name=parts[0],
                        last_name=parts[1] if len(parts) > 1 else '',
                    )
                    driver_profile = DriverProfile.objects.create(
                        user=new_user,
                        phone_number=form.cleaned_data['phone_number'],
                        national_id=form.cleaned_data['national_id'],
                        profile_photo=form.cleaned_data.get('profile_photo'),
                        id_front=form.cleaned_data.get('id_front'),
                        id_back=form.cleaned_data.get('id_back'),
                        driver_license=form.cleaned_data.get('driver_license'),
                        verification_status=DriverProfile.VerificationStatus.PENDING,
                    )
                    driver_group, _ = Group.objects.get_or_create(name='Driver')
                    new_user.groups.add(driver_group)

                request.session['driver_reg_profile_id'] = driver_profile.id
                request.session['driver_reg_step2'] = True
                login(request, new_user)
                return redirect('drivers:driver_register_step3')

            except IntegrityError:
                messages.error(request, 'This email is already registered.', 'alert-danger')
            except Exception as e:
                messages.error(request, 'Could not create account. Please try again.', 'alert-danger')
                print(f"[Step2 Error] {e}")
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')
            print(f"[Step2 Form Errors] {form.errors}")  # debug (no passwords printed)

    return render(request, 'drivers/register_step2.html', {'form': form, 'current_step': 2})



def driver_register_step3(request: HttpRequest):
    if not request.session.get('driver_reg_step2'):
        return redirect('drivers:driver_register_step2')

    profile_id = request.session.get('driver_reg_profile_id')
    driver_profile = get_object_or_404(DriverProfile, id=profile_id)

    try:
        existing_vehicle = driver_profile.vehicle
    except Vehicle.DoesNotExist:
        existing_vehicle = None

    form = VehicleForm(instance=existing_vehicle)

    if request.method == 'POST':
        form = VehicleForm(request.POST, request.FILES, instance=existing_vehicle)
        if form.is_valid():
            vehicle = form.save(commit=False)
            vehicle.driver = driver_profile
            vehicle.save()
            request.session['driver_reg_step3'] = True
            return redirect('drivers:driver_register_step4')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'drivers/register_step3.html', {'form': form, 'current_step': 3})



def _ensure_default_routes():
    """
    Auto-create a small set of default Riyadh routes if the database is empty.
    This prevents Step 4 from showing an empty list during development.
    """
    if Route.objects.count() == 0:
        defaults = [
            ('Al Narjis', 'Al Malqa'),
            ('Al Malqa', 'Al Narjis'),
            ('Al Yarmouk', 'Al Sulaimaniyah'),
            ('Al Sulaimaniyah', 'Al Yarmouk'),
            ('Al Olaya', 'Al Rahmaniyah'),
            ('Al Rahmaniyah', 'Al Olaya'),
            ('Al Rayyan', 'Ad Dar Al Baida'),
            ('Ad Dar Al Baida', 'Al Rayyan'),
            ('Al Sulay', 'King Khalid Airport'),
            ('King Khalid Airport', 'Al Sulay'),
            ('Al Malqa', 'Al Nakheel'),
            ('Al Nakheel', 'Al Malqa'),
            ('Al Yasmin', 'King Abdullah Financial District'),
            ('King Abdullah Financial District', 'Al Yasmin'),
            ('Al Murooj', 'Al Taawun'),
            ('Al Taawun', 'Al Murooj'),
            ('Hittin', 'Al Sahafah'),
            ('Al Sahafah', 'Hittin'),
            ('Qurtubah', 'Al Malaz'),
            ('Al Malaz', 'Qurtubah'),
        ]
        for from_area, to_area in defaults:
            Route.objects.get_or_create(from_area=from_area, to_area=to_area, city='Riyadh')


def _ensure_default_plans():
    """
    Auto-create default subscription plans if none exist.
    """
    if SubscriptionPlan.objects.count() == 0:
        defaults = [
            {'name': '7-Day Free Trial', 'price': 0, 'duration_days': 7, 'description': 'Free trial for new drivers.'},
            {'name': 'Monthly Plan', 'price': 149, 'duration_days': 30, 'description': 'Monthly subscription for active drivers.'},
            {'name': 'Quarterly Plan', 'price': 399, 'duration_days': 90, 'description': 'Quarterly subscription with discounted price.'},
            {'name': 'Yearly Plan', 'price': 1499, 'duration_days': 365, 'description': 'Annual subscription for professional drivers.'},
        ]
        for d in defaults:
            SubscriptionPlan.objects.get_or_create(name=d['name'], defaults=d)


def driver_register_step4(request: HttpRequest):
    if not request.session.get('driver_reg_step3'):
        return redirect('drivers:driver_register_step3')

    _ensure_default_routes()

    routes = Route.objects.all().order_by('from_area', 'to_area')

    if request.method == 'POST':
        selected_route_ids = request.POST.getlist('routes')
        if not selected_route_ids:
            messages.error(request, 'Please select at least one route.', 'alert-danger')
        else:
            request.session['driver_reg_selected_routes'] = selected_route_ids
            request.session['driver_reg_step4'] = True
            return redirect('drivers:driver_register_step5')

    return render(request, 'drivers/register_step4.html', {
        'routes': routes,
        'current_step': 4,
    })



def driver_register_step5(request: HttpRequest):
    if not request.session.get('driver_reg_step4'):
        return redirect('drivers:driver_register_step4')

    profile_id = request.session.get('driver_reg_profile_id')
    driver_profile = get_object_or_404(DriverProfile, id=profile_id)
    selected_route_ids = request.session.get('driver_reg_selected_routes', [])
    selected_routes = Route.objects.filter(id__in=selected_route_ids)

    if request.method == 'POST':
        all_valid = True
        for route in selected_routes:
            prefix = f'route_{route.id}_'
            days = request.POST.getlist(f'{prefix}days')
            start_time = request.POST.get(f'{prefix}start_time')
            end_time = request.POST.get(f'{prefix}end_time')
            price = request.POST.get(f'{prefix}price')
            if not days or not start_time or not end_time or not price:
                all_valid = False
                messages.error(request, f'Please fill all fields for: {route}', 'alert-danger')
                break

        if all_valid:
            try:
                with transaction.atomic():
                    for route in selected_routes:
                        prefix = f'route_{route.id}_'
                        days_str = ','.join(request.POST.getlist(f'{prefix}days'))
                        start_t  = request.POST.get(f'{prefix}start_time')
                        end_t    = request.POST.get(f'{prefix}end_time')
                        price    = request.POST.get(f'{prefix}price')
                        commitment = request.POST.get(f'{prefix}commitment', '1')
                        obj, created = DriverRoute.objects.get_or_create(
                            driver=driver_profile,
                            route=route,
                            defaults={
                                'available_days': days_str,
                                'start_time': start_t,
                                'end_time': end_t,
                                'monthly_price': price,
                                'commitment_duration': commitment,
                                'is_active': True,
                            }
                        )
                        if not created:
                            obj.available_days = days_str
                            obj.start_time = start_t
                            obj.end_time = end_t
                            obj.monthly_price = price
                            obj.commitment_duration = commitment
                            obj.is_active = True
                            obj.save()
                request.session['driver_reg_step5'] = True
                return redirect('drivers:driver_register_step6')
            except Exception as e:
                messages.error(request, 'Could not save routes. Please try again.', 'alert-danger')
                print(f"[Step5 Error] {e}")

    return render(request, 'drivers/register_step5.html', {
        'selected_routes': selected_routes,
        'current_step': 5,
        'days_choices': ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'],
        'commitment_choices': DriverRoute.CommitmentDuration.choices,
        'time_choices': [f'{h:02d}:00' for h in range(24)],
    })



def driver_register_step6(request: HttpRequest):
    """
    Step 6: Driver selects subscription plan.
    - Free Trial: creates subscription directly, no payment needed.
    - Paid plan: creates pending DriverSubscriptionPayment, renders Moyasar form inline.
    SAFE: no raw card data collected or stored here — Moyasar handles card data.
    """
    from django.conf import settings as django_settings

    if not request.session.get('driver_reg_step5'):
        return redirect('drivers:driver_register_step5')

    profile_id = request.session.get('driver_reg_profile_id')
    driver_profile = get_object_or_404(DriverProfile, id=profile_id)

    _ensure_default_plans()
    plans = SubscriptionPlan.objects.filter(is_active=True)

    errors = []
    selected_plan_id = None
    pending_payment = None
    moyasar_key = getattr(django_settings, 'MOYASAR_PUBLISHABLE_KEY', '')

    if request.method == 'POST':
        plan_id = request.POST.get('plan_id')
        selected_plan_id = plan_id

        if not plan_id:
            errors.append('Please select a subscription plan.')

        plan = None
        if plan_id:
            try:
                plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
            except SubscriptionPlan.DoesNotExist:
                errors.append('Selected plan is not valid.')

        if not errors and plan:
            if plan.price == 0:
                from datetime import timedelta
                today = timezone.now().date()
                DriverSubscription.objects.filter(driver=driver_profile, is_active=True).update(is_active=False)
                DriverSubscription.objects.create(
                    driver=driver_profile,
                    plan=plan,
                    start_date=today,
                    end_date=today + timedelta(days=plan.duration_days),
                    is_active=True,
                )
                request.session['driver_reg_step6'] = True
                messages.success(request, 'Free trial activated!', 'alert-success')
                return redirect('drivers:driver_register_step7')
            else:
                pending_payment = DriverSubscriptionPayment.objects.create(
                    driver=driver_profile,
                    plan=plan,
                    amount=plan.price,
                    status=DriverSubscriptionPayment.PaymentStatus.PENDING,
                )
                request.session['pending_sub_payment_id'] = pending_payment.id

                if not moyasar_key:
                    return redirect('drivers:driver_subscription_payment', payment_id=pending_payment.id)

    for e in errors:
        messages.error(request, e, 'alert-danger')

    context = {
        'plans': plans,
        'current_step': 6,
        'selected_plan_id': selected_plan_id,
        'pending_payment': pending_payment,
        'moyasar_key': moyasar_key,
    }
    if pending_payment:
        context['amount_halalas'] = int(pending_payment.amount * 100)

    return render(request, 'drivers/register_step6.html', context)



def moyasar_payment_callback(request: HttpRequest, payment_id: int):
    """
    Secure callback for Moyasar after user completes payment.
    Verifies the payment status via Moyasar API using the secret key
    (NEVER trust the redirect URL parameters alone — they can be tampered with).
    """
    from django.conf import settings as django_settings
    try:
        import requests
    except ImportError:
        messages.error(request, 'Payment library not available. Please contact support.', 'alert-danger')
        return redirect('drivers:driver_register_step6')

    sub_payment = get_object_or_404(DriverSubscriptionPayment, id=payment_id)

    try:
        if sub_payment.driver != request.user.driverprofile:
            messages.error(request, 'Access denied.', 'alert-danger')
            return redirect('main:landing')
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    if sub_payment.status == DriverSubscriptionPayment.PaymentStatus.PAID:
        request.session['driver_reg_step6'] = True
        return redirect('drivers:driver_register_step7')

    moyasar_payment_id = request.GET.get('id', '').strip()
    moyasar_status = request.GET.get('status', '').strip()

    if not moyasar_payment_id:
        messages.error(request, 'Payment reference missing.', 'alert-danger')
        return redirect('drivers:driver_register_step6')

    secret_key = getattr(django_settings, 'MOYASAR_SECRET_KEY', '')
    if not secret_key:
        messages.error(request, 'Payment gateway not configured.', 'alert-danger')
        return redirect('drivers:driver_register_step6')

    try:
        api_response = requests.get(
            f'https://api.moyasar.com/v1/payments/{moyasar_payment_id}',
            auth=(secret_key, ''),
            timeout=15,
        )
    except requests.RequestException:
        messages.error(request, 'Could not verify payment. Please try again.', 'alert-danger')
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.FAILED
        sub_payment.save()
        return redirect('drivers:driver_register_step6')

    if api_response.status_code != 200:
        messages.error(request, 'Payment verification failed.', 'alert-danger')
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.FAILED
        sub_payment.save()
        return redirect('drivers:driver_register_step6')

    data = api_response.json()
    verified_status = data.get('status', '')
    verified_amount = data.get('amount', 0)  # in halalas
    expected_amount = int(sub_payment.amount * 100)

    if verified_amount != expected_amount:
        messages.error(request, 'Payment amount mismatch.', 'alert-danger')
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.FAILED
        sub_payment.save()
        return redirect('drivers:driver_register_step6')

    if verified_status == 'paid':
        from datetime import timedelta
        today = timezone.now().date()
        DriverSubscription.objects.filter(driver=sub_payment.driver, is_active=True).update(is_active=False)
        sub = DriverSubscription.objects.create(
            driver=sub_payment.driver,
            plan=sub_payment.plan,
            start_date=today,
            end_date=today + timedelta(days=sub_payment.plan.duration_days),
            is_active=True,
        )
        sub_payment.subscription = sub
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.PAID
        sub_payment.paid_at = timezone.now()
        sub_payment.payment_reference = moyasar_payment_id
        source = data.get('source', {}) or {}
        if isinstance(source, dict):
            sub_payment.card_last4 = (source.get('number', '') or '')[-4:]
        sub_payment.save()

        request.session['driver_reg_step6'] = True
        messages.success(request, 'Payment confirmed! Your subscription is now active.', 'alert-success')
        return redirect('drivers:driver_register_step7')
    else:
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.FAILED
        sub_payment.save()
        messages.error(request, f'Payment was not completed (status: {verified_status}). Please try again.', 'alert-danger')
        return redirect('drivers:driver_register_step6')


def driver_register_step7(request):
    if not request.session.get('driver_reg_step6'):
        request.session['driver_reg_step6'] = True

    profile_id = request.session.get('driver_reg_profile_id')
    driver_profile = get_object_or_404(DriverProfile, id=profile_id)

    if request.method == 'POST':
        for key in [
            'driver_reg_step1', 'driver_reg_step2', 'driver_reg_step3',
            'driver_reg_step4', 'driver_reg_step5', 'driver_reg_step6',
            'driver_reg_profile_id', 'driver_reg_selected_routes'
        ]:
            request.session.pop(key, None)
        messages.success(
            request,
            'Registration complete! Your profile is under review. We will notify you once approved.',
            'alert-success'
        )
        return redirect('main:landing')

    return render(request, 'drivers/register_step7.html', {
        'driver_profile': driver_profile,
        'current_step': 7,
    })



@login_required(login_url='/accounts/signin/')
def driver_dashboard(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        messages.error(request, 'Driver profile not found.', 'alert-danger')
        return redirect('main:landing')

    if driver_profile.verification_status != DriverProfile.VerificationStatus.APPROVED:
        return render(request, 'drivers/pending_approval.html', {
            'driver_profile': driver_profile,
        })

    from bookings.models import Booking, Rating as BookingRating

    today = timezone.now().date()
    total_trips = Booking.objects.filter(driver=driver_profile).count()
    active_bookings = Booking.objects.filter(driver=driver_profile, status='active').count()
    recent_ratings = BookingRating.objects.filter(driver=driver_profile).order_by('-created_at')[:5]

    from bookings.models import Payment
    monthly_earnings = Payment.objects.filter(
        booking__driver=driver_profile,
        status='paid',
        paid_at__year=today.year,
        paid_at__month=today.month,
    ).aggregate(total=Sum('amount'))['total'] or 0

    upcoming = Booking.objects.filter(
        driver=driver_profile,
        status='confirmed',
        start_date__gte=today
    ).order_by('start_date').first()

    return render(request, 'drivers/dashboard.html', {
        'driver_profile': driver_profile,
        'total_trips': total_trips,
        'active_bookings': active_bookings,
        'monthly_earnings': monthly_earnings,
        'recent_ratings': recent_ratings,
        'upcoming': upcoming,
    })



def driver_profile_view(request: HttpRequest, driver_id: int):
    driver_profile = get_object_or_404(DriverProfile, id=driver_id, verification_status='approved')

    try:
        vehicle = driver_profile.vehicle
    except Vehicle.DoesNotExist:
        vehicle = None

    driver_routes = DriverRoute.objects.filter(driver=driver_profile, is_active=True)

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Rating
    ratings = Rating.objects.filter(driver=driver_profile).order_by('-created_at')[:5]

    is_favorite = False
    if request.user.is_authenticated:
        try:
            passenger_profile = request.user.passengerprofile
            is_favorite = FavoriteDriver.objects.filter(
                passenger=passenger_profile, driver=driver_profile
            ).exists()
        except PassengerProfile.DoesNotExist:
            pass

    return render(request, 'drivers/driver_profile.html', {
        'driver_profile': driver_profile,
        'vehicle': vehicle,
        'driver_routes': driver_routes,
        'ratings': ratings,
        'is_favorite': is_favorite,
    })



def search_drivers(request: HttpRequest):
    drivers = DriverRoute.objects.filter(
        driver__verification_status='approved',
        is_active=True
    ).select_related('driver', 'route', 'driver__vehicle')

    from_area  = request.GET.get('from_area', '').strip()
    to_area    = request.GET.get('to_area', '').strip()
    car_type   = request.GET.get('car_type', '').strip()
    min_rating = request.GET.get('min_rating', '').strip()
    max_price  = request.GET.get('max_price', '').strip()
    sort_by    = request.GET.get('sort_by', 'rating')
    from_time  = request.GET.get('from_time', '').strip()
    to_time    = request.GET.get('to_time', '').strip()

    if from_area:
        drivers = drivers.filter(route__from_area__icontains=from_area)
    if to_area:
        drivers = drivers.filter(route__to_area__icontains=to_area)
    if car_type:
        drivers = drivers.filter(driver__vehicle__car_type=car_type)
    if min_rating:
        try:
            drivers = drivers.filter(driver__average_rating__gte=float(min_rating))
        except ValueError:
            pass
    if max_price:
        try:
            drivers = drivers.filter(monthly_price__lte=float(max_price))
        except ValueError:
            pass
    if from_time:
        drivers = drivers.filter(start_time__lte=from_time)
    if to_time:
        drivers = drivers.filter(end_time__gte=to_time)

    if sort_by == 'price_low':
        drivers = drivers.order_by('monthly_price')
    elif sort_by == 'price_high':
        drivers = drivers.order_by('-monthly_price')
    else:
        drivers = drivers.order_by('-driver__average_rating')

    paginator = Paginator(drivers, 9)
    page_number = request.GET.get('page', 1)
    drivers_page = paginator.get_page(page_number)

    time_choices = [f'{h:02d}:00' for h in range(24)]

    return render(request, 'drivers/search.html', {
        'drivers': drivers_page,
        'routes': Route.objects.all(),
        'car_types': Vehicle.CarType.choices,
        'from_area': from_area,
        'to_area': to_area,
        'car_type': car_type,
        'min_rating': min_rating,
        'max_price': max_price,
        'sort_by': sort_by,
        'from_time': from_time,
        'to_time': to_time,
        'time_choices': time_choices,
    })



@login_required(login_url='/accounts/signin/')
def toggle_favorite(request: HttpRequest, driver_id: int):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Only passengers can add favorites.', 'alert-danger')
        return redirect('drivers:driver_profile_view', driver_id=driver_id)

    driver_profile = get_object_or_404(DriverProfile, id=driver_id)
    existing = FavoriteDriver.objects.filter(passenger=passenger_profile, driver=driver_profile).first()

    if existing:
        existing.delete()
        messages.success(request, 'Driver removed from favorites.', 'alert-warning')
    else:
        FavoriteDriver.objects.create(passenger=passenger_profile, driver=driver_profile)
        messages.success(request, 'Driver added to favorites!', 'alert-success')

    return redirect('drivers:driver_profile_view', driver_id=driver_id)



@login_required(login_url='/accounts/signin/')
def my_favorites(request: HttpRequest):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Only passengers can view favorites.', 'alert-danger')
        return redirect('main:landing')

    favorites = FavoriteDriver.objects.filter(
        passenger=passenger_profile
    ).select_related('driver__vehicle')

    return render(request, 'drivers/my_favorites.html', {'favorites': favorites})



@login_required(login_url='/accounts/signin/')
def driver_settings(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        messages.error(request, 'Driver profile not found.', 'alert-danger')
        return redirect('main:landing')

    try:
        vehicle = driver_profile.vehicle
    except Vehicle.DoesNotExist:
        vehicle = None

    profile_form = DriverProfileUpdateForm(instance=driver_profile)
    vehicle_form = VehicleForm(instance=vehicle) if vehicle else VehicleForm()

    if request.method == 'POST':
        profile_form = DriverProfileUpdateForm(request.POST, request.FILES, instance=driver_profile)
        vehicle_form = VehicleForm(
            request.POST, request.FILES,
            instance=vehicle if vehicle else None
        )
        if profile_form.is_valid() and vehicle_form.is_valid():
            try:
                with transaction.atomic():
                    profile_form.save()
                    v = vehicle_form.save(commit=False)
                    v.driver = driver_profile
                    v.save()
                messages.success(request, 'Settings saved successfully.', 'alert-success')
                return redirect('drivers:driver_settings')
            except Exception as e:
                messages.error(request, 'Could not save settings.', 'alert-danger')
                print(e)

    return render(request, 'drivers/settings.html', {
        'profile_form': profile_form,
        'vehicle_form': vehicle_form,
        'driver_profile': driver_profile,
    })



@login_required(login_url='/accounts/signin/')
def driver_trips(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Booking
    bookings = Booking.objects.filter(driver=driver_profile).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    if status_filter:
        bookings = bookings.filter(status=status_filter)

    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page', 1)
    bookings_page = paginator.get_page(page_number)

    from bookings.models import Booking as B
    return render(request, 'drivers/trips.html', {
        'bookings': bookings_page,
        'status_filter': status_filter,
        'status_choices': B.BookingStatus.choices,
        'driver_profile': driver_profile,
    })



@login_required(login_url='/accounts/signin/')
def trips_table(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Booking
    bookings = Booking.objects.filter(
        driver=driver_profile
    ).order_by('start_date').select_related('passenger__user', 'driver_route__route')

    return render(request, 'drivers/trips_table.html', {
        'bookings': bookings,
        'driver_profile': driver_profile,
    })



@login_required(login_url='/accounts/signin/')
def subscribers(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Booking
    today = timezone.now().date()

    all_bookings = Booking.objects.filter(driver=driver_profile).select_related('passenger__user')
    active_count = all_bookings.filter(status='active').count()
    confirmed_count = all_bookings.filter(status='confirmed').count()
    total_count = all_bookings.count()

    status_filter = request.GET.get('status', '')
    if status_filter:
        all_bookings = all_bookings.filter(status=status_filter)

    paginator = Paginator(all_bookings.order_by('-created_at'), 10)
    page_number = request.GET.get('page', 1)
    bookings_page = paginator.get_page(page_number)

    from bookings.models import Booking as B
    return render(request, 'drivers/subscribers.html', {
        'bookings': bookings_page,
        'active_count': active_count,
        'confirmed_count': confirmed_count,
        'total_count': total_count,
        'status_filter': status_filter,
        'status_choices': B.BookingStatus.choices,
        'driver_profile': driver_profile,
    })



@login_required(login_url='/accounts/signin/')
@login_required(login_url='/accounts/signin/')
def earnings(request: HttpRequest):
    """Driver earnings page with bank account payout settings."""
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Payment
    from datetime import timedelta
    today = timezone.now().date()
    week_start = today - timedelta(days=today.weekday())

    payments = Payment.objects.filter(
        booking__driver=driver_profile,
        status='paid'
    ).order_by('-paid_at')

    total_earnings   = payments.aggregate(t=Sum('amount'))['t'] or 0
    monthly_earnings = payments.filter(
        paid_at__year=today.year, paid_at__month=today.month
    ).aggregate(t=Sum('amount'))['t'] or 0
    weekly_earnings  = payments.filter(
        paid_at__date__gte=week_start
    ).aggregate(t=Sum('amount'))['t'] or 0
    today_earnings   = payments.filter(
        paid_at__date=today
    ).aggregate(t=Sum('amount'))['t'] or 0

    try:
        bank_account = driver_profile.bank_account
    except DriverBankAccount.DoesNotExist:
        bank_account = None

    bank_form = DriverBankAccountForm(instance=bank_account)

    if request.method == 'POST':
        bank_form = DriverBankAccountForm(request.POST, instance=bank_account)
        if bank_form.is_valid():
            saved = bank_form.save(commit=False)
            saved.driver = driver_profile
            saved.save()
            messages.success(request, 'Bank account saved successfully.', 'alert-success')
            return redirect('drivers:earnings')

    paginator = Paginator(payments, 10)
    page_number = request.GET.get('page', 1)
    payments_page = paginator.get_page(page_number)

    return render(request, 'drivers/earnings.html', {
        'payments': payments_page,
        'total_earnings': total_earnings,
        'monthly_earnings': monthly_earnings,
        'weekly_earnings': weekly_earnings,
        'today_earnings': today_earnings,
        'driver_profile': driver_profile,
        'bank_account': bank_account,
        'bank_form': bank_form,
    })



@login_required(login_url='/accounts/signin/')
def driver_ratings(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from bookings.models import Rating
    ratings = Rating.objects.filter(driver=driver_profile).order_by('-created_at')

    paginator = Paginator(ratings, 10)
    page_number = request.GET.get('page', 1)
    ratings_page = paginator.get_page(page_number)

    total_count = ratings.count()
    avg = ratings.aggregate(a=Avg('stars'))['a'] or 0

    return render(request, 'drivers/ratings.html', {
        'ratings': ratings_page,
        'driver_profile': driver_profile,
        'total_count': total_count,
        'average_rating': round(avg, 2),
    })



@login_required(login_url='/accounts/signin/')
def driver_complaints(request: HttpRequest):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    block = _pending_block(request, driver_profile)
    if block: return block

    from support.models import Complaint
    complaints = Complaint.objects.filter(
        booking__driver=driver_profile
    ).order_by('-created_at')

    paginator = Paginator(complaints, 10)
    page_number = request.GET.get('page', 1)
    complaints_page = paginator.get_page(page_number)

    return render(request, 'drivers/complaints.html', {
        'complaints': complaints_page,
        'driver_profile': driver_profile,
    })



@login_required(login_url='/accounts/signin/')
def submit_cancellation_request(request: HttpRequest, booking_id: int):
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    from bookings.models import Booking
    booking = get_object_or_404(Booking, id=booking_id, driver=driver_profile)

    if DriverCancellationRequest.objects.filter(booking=booking, status='pending').exists():
        messages.warning(request, 'A cancellation request for this booking is already pending.', 'alert-warning')
        return redirect('drivers:driver_trips')

    if request.method == 'POST':
        reason = request.POST.get('reason', '').strip()
        if not reason:
            messages.error(request, 'Please provide a reason for cancellation.', 'alert-danger')
        else:
            DriverCancellationRequest.objects.create(
                booking=booking,
                driver=driver_profile,
                reason=reason,
            )
            messages.success(request, 'Cancellation request submitted. Admin will review it.', 'alert-success')
            return redirect('drivers:driver_trips')

    return render(request, 'drivers/cancellation_request.html', {'booking': booking})



@login_required(login_url='/accounts/signin/')
def driver_subscription_payment(request: HttpRequest, payment_id: int):
    """
    Payment page for driver platform subscription.
    Simulation (default) or Moyasar if keys configured.
    SAFE: no raw card data collected here.
    """
    from django.conf import settings as django_settings
    sub_payment = get_object_or_404(DriverSubscriptionPayment, id=payment_id)

    try:
        driver_profile = request.user.driverprofile
        if sub_payment.driver != driver_profile:
            messages.error(request, 'Access denied.', 'alert-danger')
            return redirect('main:landing')
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    if sub_payment.status == DriverSubscriptionPayment.PaymentStatus.PAID:
        messages.info(request, 'This subscription payment has already been completed.', 'alert-info')
        return redirect('drivers:driver_register_step7')

    moyasar_key = getattr(django_settings, 'MOYASAR_PUBLISHABLE_KEY', '')
    use_simulation = not bool(moyasar_key)
    amount_halalas = int(sub_payment.amount * 100)

    return render(request, 'drivers/subscription_payment.html', {
        'sub_payment': sub_payment,
        'plan': sub_payment.plan,
        'use_simulation': use_simulation,
        'moyasar_key': moyasar_key,
        'amount_halalas': amount_halalas,
    })


@login_required(login_url='/accounts/signin/')
def simulate_subscription_payment_success(request: HttpRequest, payment_id: int):
    """Simulation: marks driver subscription payment as paid."""
    if request.method != 'POST':
        return redirect('drivers:driver_dashboard')

    sub_payment = get_object_or_404(DriverSubscriptionPayment, id=payment_id)

    try:
        if sub_payment.driver != request.user.driverprofile:
            return redirect('main:landing')
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    if sub_payment.status == DriverSubscriptionPayment.PaymentStatus.PENDING:
        from datetime import timedelta
        today = timezone.now().date()
        DriverSubscription.objects.filter(driver=sub_payment.driver, is_active=True).update(is_active=False)
        sub = DriverSubscription.objects.create(
            driver=sub_payment.driver,
            plan=sub_payment.plan,
            start_date=today,
            end_date=today + timedelta(days=sub_payment.plan.duration_days),
            is_active=True,
        )
        sub_payment.subscription = sub
        sub_payment.status = DriverSubscriptionPayment.PaymentStatus.PAID
        sub_payment.paid_at = timezone.now()
        sub_payment.payment_reference = f"SIM-{sub_payment.id}-{timezone.now().strftime('%Y%m%d%H%M%S')}"
        sub_payment.card_last4 = '0000'
        sub_payment.save()

        request.session['driver_reg_step6'] = True
        messages.success(request, 'Subscription payment confirmed!', 'alert-success')
        return redirect('drivers:driver_register_step7')

    messages.warning(request, 'Payment already processed.', 'alert-warning')
    return redirect('drivers:driver_register_step7')


@login_required(login_url='/accounts/signin/')
def simulate_subscription_payment_failed(request: HttpRequest, payment_id: int):
    """Simulation: marks driver subscription payment as failed."""
    if request.method != 'POST':
        return redirect('drivers:driver_dashboard')

    sub_payment = get_object_or_404(DriverSubscriptionPayment, id=payment_id)
    sub_payment.status = DriverSubscriptionPayment.PaymentStatus.FAILED
    sub_payment.save()

    messages.error(request, 'Payment failed. Please try again.', 'alert-danger')
    return redirect('drivers:driver_register_step6')



def _get_driver_or_redirect(request):
    """
    Returns (driver_profile, None) on success,
    or (None, redirect_response) if no profile found.
    """
    try:
        return request.user.driverprofile, None
    except DriverProfile.DoesNotExist:
        messages.error(request, 'Driver profile not found.', 'alert-danger')
        return None, redirect('main:landing')


def _pending_block(request, driver_profile):
    """
    If driver is not approved, render pending_approval.html.
    Returns a response object, or None if driver is approved.
    Usage:
        block = _pending_block(request, driver_profile)
        if block: return block
    """
    if driver_profile.verification_status != DriverProfile.VerificationStatus.APPROVED:
        return render(request, 'drivers/pending_approval.html', {'driver_profile': driver_profile})
    return None



@login_required(login_url='/accounts/signin/')
def driver_more(request: HttpRequest):
    """Driver 'More' menu — list of additional pages."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err
    return render(request, 'drivers/more.html', {'driver_profile': driver_profile})



@login_required(login_url='/accounts/signin/')
def driver_profile_page(request: HttpRequest):
    """Driver's own profile view — personal info, vehicle, documents."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err
    try:
        vehicle = driver_profile.vehicle
    except Vehicle.DoesNotExist:
        vehicle = None
    return render(request, 'drivers/profile_page.html', {
        'driver_profile': driver_profile,
        'vehicle': vehicle,
    })



@login_required(login_url='/accounts/signin/')
def driver_messages(request: HttpRequest):
    """
    Simple messages placeholder.
    No full chat model exists yet — shows UI layout with empty state.
    """
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err
    return render(request, 'drivers/messages_page.html', {'driver_profile': driver_profile})



@login_required(login_url='/accounts/signin/')
def driver_tickets(request: HttpRequest):
    """Driver's support tickets — uses support.models.Ticket."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    try:
        from support.models import Ticket
        tickets_qs = Ticket.objects.filter(submitted_by=request.user).order_by('-created_at')
        search = request.GET.get('search', '').strip()
        if search:
            tickets_qs = tickets_qs.filter(subject__icontains=search)
        paginator = Paginator(tickets_qs, 10)
        page_number = request.GET.get('page', 1)
        tickets_page = paginator.get_page(page_number)
        ticket_error = None
    except Exception as e:
        tickets_page = []
        search = ''
        ticket_error = 'Could not load tickets.'
        print(f"[Tickets Error] {e}")

    return render(request, 'drivers/tickets_page.html', {
        'driver_profile': driver_profile,
        'tickets': tickets_page,
        'search': search,
        'ticket_error': ticket_error,
    })



@login_required(login_url='/accounts/signin/')
def driver_subscription(request: HttpRequest):
    """Driver's platform subscription — current plan and history."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    current_sub = DriverSubscription.objects.filter(
        driver=driver_profile, is_active=True
    ).order_by('-created_at').first()

    all_subs = DriverSubscription.objects.filter(
        driver=driver_profile
    ).order_by('-created_at')

    available_plans = SubscriptionPlan.objects.filter(is_active=True)

    return render(request, 'drivers/subscription_page.html', {
        'driver_profile': driver_profile,
        'current_sub': current_sub,
        'all_subs': all_subs,
        'available_plans': available_plans,
    })



@login_required(login_url='/accounts/signin/')
def driver_invoices(request: HttpRequest):
    """Invoices related to this driver's bookings."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    try:
        from bookings.models import Invoice
        invoices = Invoice.objects.filter(
            booking__driver=driver_profile
        ).order_by('-issued_date')
        paginator = Paginator(invoices, 10)
        page_number = request.GET.get('page', 1)
        invoices_page = paginator.get_page(page_number)
    except Exception as e:
        invoices_page = []
        print(f"[Driver Invoices Error] {e}")

    return render(request, 'drivers/driver_invoices_page.html', {
        'driver_profile': driver_profile,
        'invoices': invoices_page,
    })



@login_required(login_url='/accounts/signin/')
def driver_privacy(request: HttpRequest):
    """Simple privacy policy page for drivers."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err
    return render(request, 'drivers/privacy_page.html', {'driver_profile': driver_profile})



@login_required(login_url='/accounts/signin/')
def service_settings(request: HttpRequest):
    """
    Driver Service Settings page.
    Allows driver to update vehicle info and manage their routes.
    """
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    try:
        vehicle = driver_profile.vehicle
    except Vehicle.DoesNotExist:
        vehicle = None

    vehicle_form = VehicleForm(instance=vehicle)
    driver_routes = DriverRoute.objects.filter(driver=driver_profile).order_by('route__from_area')

    if request.method == 'POST' and 'save_vehicle' in request.POST:
        vehicle_form = VehicleForm(request.POST, request.FILES, instance=vehicle)
        if vehicle_form.is_valid():
            v = vehicle_form.save(commit=False)
            v.driver = driver_profile
            v.save()
            messages.success(request, 'Vehicle information updated successfully.', 'alert-success')
            return redirect('drivers:service_settings')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    all_routes = Route.objects.all().order_by('from_area', 'to_area')

    return render(request, 'drivers/service_settings.html', {
        'driver_profile': driver_profile,
        'vehicle': vehicle,
        'vehicle_form': vehicle_form,
        'driver_routes': driver_routes,
        'all_routes': all_routes,
    })


@login_required(login_url='/accounts/signin/')
def add_driver_route(request: HttpRequest):
    """Add a new route for the driver."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    _ensure_default_routes()
    form = DriverRouteForm()

    if request.method == 'POST':
        form = DriverRouteForm(request.POST)
        if form.is_valid():
            route = form.cleaned_data['route']
            if DriverRoute.objects.filter(driver=driver_profile, route=route, is_active=True).exists():
                messages.error(request, 'You already have an active route for this selection. Please edit the existing one.', 'alert-danger')
            else:
                dr = form.save(commit=False)
                dr.driver = driver_profile
                dr.is_active = True
                dr.save()
                messages.success(request, 'Route added successfully.', 'alert-success')
                return redirect('drivers:service_settings')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'drivers/add_driver_route.html', {
        'form': form,
        'driver_profile': driver_profile,
    })


@login_required(login_url='/accounts/signin/')
def edit_driver_route(request: HttpRequest, route_id: int):
    """Edit an existing driver route."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    driver_route = get_object_or_404(DriverRoute, id=route_id, driver=driver_profile)
    form = DriverRouteForm(instance=driver_route)

    if request.method == 'POST':
        form = DriverRouteForm(request.POST, instance=driver_route)
        if form.is_valid():
            form.save()
            messages.success(request, 'Route updated successfully.', 'alert-success')
            return redirect('drivers:service_settings')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'drivers/edit_driver_route.html', {
        'form': form,
        'driver_route': driver_route,
        'driver_profile': driver_profile,
    })


@login_required(login_url='/accounts/signin/')
def deactivate_driver_route(request: HttpRequest, route_id: int):
    """Deactivate (soft-delete) a driver route."""
    driver_profile, err = _get_driver_or_redirect(request)
    if err:
        return err

    driver_route = get_object_or_404(DriverRoute, id=route_id, driver=driver_profile)

    if request.method == 'POST':
        driver_route.is_active = False
        driver_route.save()
        messages.success(request, 'Route deactivated. Passengers can no longer book this route.', 'alert-warning')
        return redirect('drivers:service_settings')

    return render(request, 'drivers/confirm_deactivate_route.html', {
        'driver_route': driver_route,
    })
