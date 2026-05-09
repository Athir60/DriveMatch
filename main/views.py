from django.shortcuts import render, redirect
from django.http import HttpRequest
from django.contrib import messages

from drivers.models import DriverProfile, DriverRoute, Route, FavoriteDriver
from bookings.models import Booking
from accounts.models import PassengerProfile


def landing(request):
    if request.user.is_authenticated:
        if request.user.groups.filter(name='Driver').exists():
            return redirect('drivers:driver_dashboard')
        elif request.user.is_staff or request.user.is_superuser:
            return redirect('/admin/')
        else:
            return redirect('main:passenger_home')
    return render(request, 'main/landing.html')


def passenger_home(request):

    popular_routes = Route.objects.all()[:6]
    top_drivers = DriverRoute.objects.filter(
        driver__verification_status='approved',
        is_active=True
    ).select_related('driver', 'driver__vehicle', 'route').order_by('-driver__average_rating')[:6]

    if not request.user.is_authenticated:
        return render(request, 'main/passenger_home.html', {
            'popular_routes': popular_routes,
            'top_drivers': top_drivers,
            'is_guest': True,  # 🔥 مهم
        })

    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Passenger profile not found.', 'alert-danger')
        return redirect('main:landing')

    latest_bookings = Booking.objects.filter(
        passenger=passenger_profile
    ).order_by('-created_at')[:5]

    favorites = FavoriteDriver.objects.filter(
        passenger=passenger_profile
    ).select_related('driver', 'driver__vehicle')[:4]

    return render(request, 'main/passenger_home.html', {
        'passenger_profile': passenger_profile,
        'popular_routes': popular_routes,
        'top_drivers': top_drivers,
        'latest_bookings': latest_bookings,
        'favorites': favorites,
        'is_guest': False,
    })


def contact(request):
    return redirect('support:contact')


def terms(request):
    return render(request, 'main/terms.html')


def privacy(request):
    return render(request, 'main/privacy.html')


def about(request):
    return render(request, 'main/about.html')


def careers(request):
    return render(request, 'main/careers.html')


from django.contrib.auth.decorators import login_required


@login_required(login_url='/accounts/signin/')
def passenger_more(request):
    return render(request, 'main/passenger_more.html')


@login_required(login_url='/accounts/signin/')
def passenger_messages_redirect(request):
    return redirect('messaging:passenger_threads')