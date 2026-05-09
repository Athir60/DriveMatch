from django.db import models
from django.contrib.auth.models import User


class MessageThread(models.Model):
    """A conversation thread between a passenger and a driver."""
    passenger = models.ForeignKey(
        'accounts.PassengerProfile', on_delete=models.CASCADE, related_name='message_threads'
    )
    driver = models.ForeignKey(
        'drivers.DriverProfile', on_delete=models.CASCADE, related_name='message_threads'
    )
    booking = models.ForeignKey(
        'bookings.Booking', on_delete=models.SET_NULL, null=True, blank=True, related_name='threads'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('passenger', 'driver')   # one thread per pair
        ordering = ['-updated_at']

    def __str__(self):
        return f"Thread: {self.passenger} <-> {self.driver}"

    def last_message(self):
        return self.messages.order_by('-created_at').first()


class Message(models.Model):
    """A single message inside a thread."""
    thread = models.ForeignKey(MessageThread, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True)
    location_lat = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_lng = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    location_label = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return f"Msg from {self.sender.username} in thread #{self.thread_id}"

    @property
    def has_location(self):
        return self.location_lat is not None and self.location_lng is not None

    @property
    def maps_url(self):
        if self.has_location:
            return f"https://www.google.com/maps?q={self.location_lat},{self.location_lng}"
        return None
