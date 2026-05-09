import json
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone

from .models import Ticket, Complaint
from .forms import TicketForm, ComplaintForm, ContactForm
from bookings.models import Booking
from accounts.models import PassengerProfile


def _get_ticket_number():
    year = timezone.now().year
    last = Ticket.objects.order_by('-id').first()
    next_id = (last.id + 1) if last else 1
    return f"TCK-{year}-{str(next_id).zfill(4)}"



@login_required(login_url='/accounts/signin/')
def contact(request: HttpRequest):
    """
    Contact page — requires login.
    Creates a Ticket. If category requires a booking, booking_id is required.
    """
    user_bookings = []
    BOOKING_REQUIRED_SUBJECTS = ('booking', 'payment', 'driver', 'contract', 'dispute')

    try:
        passenger_profile = request.user.passengerprofile
        user_bookings = Booking.objects.filter(passenger=passenger_profile).order_by('-created_at')
    except PassengerProfile.DoesNotExist:
        try:
            driver_profile = request.user.driverprofile
            user_bookings = Booking.objects.filter(driver=driver_profile).order_by('-created_at')
        except Exception:
            user_bookings = []

    form = ContactForm()

    if request.method == 'POST':
        form = ContactForm(request.POST, request.FILES)
        if form.is_valid():
            subject_val = form.cleaned_data['subject']
            related_booking_id = request.POST.get('related_booking_id', '').strip()

            if subject_val in BOOKING_REQUIRED_SUBJECTS and not related_booking_id:
                messages.error(
                    request,
                    'Please select the related booking for this type of inquiry.',
                    'alert-danger'
                )
            else:
                related_id = related_booking_id or form.cleaned_data.get('related_id', '')
                Ticket.objects.create(
                    submitted_by=request.user,
                    ticket_number=_get_ticket_number(),
                    ticket_type=Ticket.TicketType.OTHER,
                    category=Ticket.TicketCategory.OTHER,
                    subject=form.cleaned_data['subject'],
                    description=form.cleaned_data['description'],
                    related_id=related_id,
                    status=Ticket.TicketStatus.OPEN,
                )
                messages.success(
                    request,
                    'Your message has been sent. We will get back to you within 24 hours.',
                    'alert-success'
                )
                return redirect('support:contact')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'support/contact.html', {
        'form': form,
        'user_bookings': user_bookings,
        'booking_required_subjects': list(BOOKING_REQUIRED_SUBJECTS),
    })



@login_required(login_url='/accounts/signin/')
def tickets(request: HttpRequest):
    all_tickets = Ticket.objects.filter(submitted_by=request.user).order_by('-created_at')

    status_filter = request.GET.get('status', '')
    type_filter = request.GET.get('ticket_type', '')
    search = request.GET.get('search', '').strip()

    if status_filter:
        all_tickets = all_tickets.filter(status=status_filter)
    if type_filter:
        all_tickets = all_tickets.filter(ticket_type=type_filter)
    if search:
        all_tickets = all_tickets.filter(subject__icontains=search)

    paginator = Paginator(all_tickets, 10)
    tickets_page = paginator.get_page(request.GET.get('page', 1))

    return render(request, 'support/tickets.html', {
        'tickets': tickets_page,
        'status_filter': status_filter,
        'type_filter': type_filter,
        'search': search,
        'status_choices': Ticket.TicketStatus.choices,
        'type_choices': Ticket.TicketType.choices,
    })



@login_required(login_url='/accounts/signin/')
def create_ticket(request: HttpRequest):
    form = TicketForm()

    if request.method == 'POST':
        form = TicketForm(request.POST, request.FILES)
        if form.is_valid():
            ticket = form.save(commit=False)
            ticket.submitted_by = request.user
            ticket.ticket_number = _get_ticket_number()
            ticket.status = Ticket.TicketStatus.OPEN
            ticket.save()
            messages.success(
                request,
                f'Ticket {ticket.ticket_number} created successfully.',
                'alert-success'
            )
            return redirect('support:tickets')
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'support/ticket_form.html', {'form': form})



@login_required(login_url='/accounts/signin/')
def create_complaint(request: HttpRequest, booking_id: int):
    try:
        passenger_profile = request.user.passengerprofile
    except PassengerProfile.DoesNotExist:
        messages.error(request, 'Only passengers can submit complaints.', 'alert-danger')
        return redirect('main:landing')

    booking = get_object_or_404(Booking, id=booking_id, passenger=passenger_profile)
    form = ComplaintForm()

    if request.method == 'POST':
        form = ComplaintForm(request.POST)
        if form.is_valid():
            complaint = form.save(commit=False)
            complaint.booking = booking
            complaint.submitted_by = request.user
            complaint.status = Complaint.ComplaintStatus.NEW
            complaint.save()
            messages.success(
                request,
                'Complaint submitted. We will review it within 24 hours.',
                'alert-success'
            )
            return redirect('bookings:booking_detail', booking_id=booking.id)
        else:
            messages.error(request, 'Please correct the errors below.', 'alert-danger')

    return render(request, 'support/complaint_form.html', {
        'form': form,
        'booking': booking,
    })
