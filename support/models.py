from django.db import models
from django.contrib.auth.models import User
from bookings.models import Booking



class Complaint(models.Model):

    class ComplaintStatus(models.TextChoices):
        NEW = 'new', 'New'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='complaints')
    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=ComplaintStatus.choices, default=ComplaintStatus.NEW)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    admin_response = models.TextField(blank=True)

    def __str__(self):
        return f"Complaint #{self.id} — {self.subject} ({self.status})"



class Ticket(models.Model):

    class TicketStatus(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        IN_REVIEW = 'in_review', 'In Review'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'

    class TicketType(models.TextChoices):
        APP_ISSUE = 'app_issue', 'App Issue'
        DRIVER_RIDER_DISPUTE = 'dispute', 'Driver & Rider Dispute'
        PAYMENT = 'payment', 'Payment'
        OTHER = 'other', 'Other'

    class TicketCategory(models.TextChoices):
        TECHNICAL = 'technical', 'Technical Problem'
        DRIVER_BEHAVIOR = 'driver_behavior', 'Driver Behavior'
        PAYMENT_ISSUE = 'payment_issue', 'Payment Issue'
        ROUTE_ISSUE = 'route_issue', 'Route Issue'
        ACCOUNT_ACCESS = 'account_access', 'Account Access'
        OTHER = 'other', 'Other'

    submitted_by = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket_number = models.CharField(max_length=20, unique=True)
    ticket_type = models.CharField(max_length=30, choices=TicketType.choices, default=TicketType.OTHER)
    category = models.CharField(max_length=30, choices=TicketCategory.choices, default=TicketCategory.OTHER)
    subject = models.CharField(max_length=200)
    description = models.TextField()
    related_id = models.CharField(max_length=50, blank=True)
    attachment = models.FileField(upload_to='documents/tickets/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=TicketStatus.choices, default=TicketStatus.OPEN)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    admin_response = models.TextField(blank=True)

    def __str__(self):
        return f"#{self.ticket_number} — {self.subject} ({self.status})"
