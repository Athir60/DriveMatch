from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages as flash
from django.utils import timezone

from .models import MessageThread, Message
from accounts.models import PassengerProfile
from drivers.models import DriverProfile
from bookings.models import Booking


def _thread_participant(request, thread):
    """Check if current user is a valid participant in this thread."""
    is_p = hasattr(request.user, 'passengerprofile') and thread.passenger == request.user.passengerprofile
    is_d = hasattr(request.user, 'driverprofile') and thread.driver == request.user.driverprofile
    return is_p or is_d, is_p, is_d


@login_required(login_url='/accounts/signin/')
def start_conversation(request: HttpRequest, driver_id: int):
    """
    Passenger opens or creates a conversation with a specific driver.
    Accessed via: GET /chat/start/<driver_id>/
    Optional: ?booking_id=<id>
    """
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        flash.error(request, 'Only passengers can start conversations.', 'alert-danger')
        return redirect('main:landing')

    driver_profile = get_object_or_404(DriverProfile, id=driver_id)

    booking_id = request.GET.get('booking_id')
    booking = None
    if booking_id:
        try:
            booking = Booking.objects.get(id=booking_id, passenger=passenger_profile, driver=driver_profile)
        except Booking.DoesNotExist:
            pass

    thread, created = MessageThread.objects.get_or_create(
        passenger=passenger_profile,
        driver=driver_profile,
        defaults={'booking': booking}
    )
    if created and booking and not thread.booking:
        thread.booking = booking
        thread.save()

    return redirect('messaging:conversation', thread_id=thread.id)


@login_required(login_url='/accounts/signin/')
def conversation(request: HttpRequest, thread_id: int):
    """Show conversation and handle sending new messages."""
    thread = get_object_or_404(MessageThread, id=thread_id)

    allowed, is_passenger, is_driver = _thread_participant(request, thread)
    if not allowed:
        flash.error(request, 'You do not have access to this conversation.', 'alert-danger')
        return redirect('main:landing')

    thread.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    chat_messages = thread.messages.select_related('sender').order_by('created_at')

    if request.method == 'POST':
        text = request.POST.get('text', '').strip()
        lat  = request.POST.get('location_lat', '').strip()
        lng  = request.POST.get('location_lng', '').strip()
        label = request.POST.get('location_label', '').strip()

        has_location = bool(lat and lng)
        if not text and not has_location:
            flash.error(request, 'Please type a message or share your location.', 'alert-danger')
        else:
            msg = Message(thread=thread, sender=request.user, text=text)
            if has_location:
                try:
                    msg.location_lat = float(lat)
                    msg.location_lng = float(lng)
                    msg.location_label = label or 'Shared location'
                except ValueError:
                    pass
            msg.save()
            thread.updated_at = timezone.now()
            thread.save(update_fields=['updated_at'])
            return redirect('messaging:conversation', thread_id=thread.id)

    return render(request, 'messaging/conversation.html', {
        'thread': thread,
        'chat_messages': chat_messages,   # named 'chat_messages' not 'messages'
        'is_passenger': is_passenger,
        'is_driver': is_driver,
    })


@login_required(login_url='/accounts/signin/')
def passenger_threads(request: HttpRequest):
    """All conversation threads for the current passenger."""
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        return redirect('main:landing')

    threads = MessageThread.objects.filter(
        passenger=passenger_profile
    ).select_related('driver__user').order_by('-updated_at')

    return render(request, 'messaging/thread_list.html', {
        'threads': threads,
        'is_passenger': True, # هذا المتغير هو ما سيستخدمه الـ HTML الآن
    })


@login_required(login_url='/accounts/signin/')
def driver_threads(request: HttpRequest):
    """All conversation threads for the current driver."""
    try:
        driver_profile = request.user.driverprofile
    except DriverProfile.DoesNotExist:
        return redirect('main:landing')

    threads = MessageThread.objects.filter(
        driver=driver_profile
    ).select_related('passenger__user').order_by('-updated_at')

    return render(request, 'messaging/thread_list.html', {
        'threads': threads,
        'is_driver': True, # هذا المتغير هو ما سيستخدمه الـ HTML الآن
    })