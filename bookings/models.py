from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from accounts.models import PassengerProfile
from drivers.models import DriverProfile, DriverRoute


class Booking(models.Model):

    class BookingStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAYMENT_PENDING = 'payment_pending', 'Payment Pending'
        CONFIRMED = 'confirmed', 'Confirmed'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        CANCELLED_BY_DRIVER = 'cancelled_by_driver', 'Cancelled by Driver'
        REFUNDED = 'refunded', 'Refunded'

    passenger = models.ForeignKey(PassengerProfile, on_delete=models.CASCADE, related_name='bookings')
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='bookings')
    driver_route = models.ForeignKey(DriverRoute, on_delete=models.PROTECT, related_name='bookings')
    subscription_months = models.IntegerField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=30, choices=BookingStatus.choices, default=BookingStatus.PENDING)
    agreed_to_terms = models.BooleanField(default=False)
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Booking #{self.id} - {self.get_status_display()}"


class Contract(models.Model):

    class ContractStatus(models.TextChoices):
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        EXPIRED = 'expired', 'Expired'
        DRIVER_CANCELLED = 'driver_cancelled', 'Driver Cancelled'
        REFUNDED = 'refunded', 'Refunded'

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='contract')
    contract_number = models.CharField(max_length=50, unique=True)
    contract_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=30, choices=ContractStatus.choices, default=ContractStatus.ACTIVE)

    def __str__(self):
        return f"Contract {self.contract_number} ({self.status})"


class Payment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    class PaymentType(models.TextChoices):
        PASSENGER_BOOKING = 'passenger_booking', 'Passenger Booking'
        DRIVER_SUBSCRIPTION = 'driver_subscription', 'Driver Subscription'

    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='payment')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_type = models.CharField(
        max_length=30, choices=PaymentType.choices, default=PaymentType.PASSENGER_BOOKING
    )
    payment_reference = models.CharField(max_length=100, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Payment #{self.id} - {self.amount} SAR - {self.status}"


class Rating(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name='rating')
    passenger = models.ForeignKey(PassengerProfile, on_delete=models.CASCADE)
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='ratings')
    stars = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.stars} stars by {self.passenger} for {self.driver}"


class Invoice(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='invoices')
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    issued_date = models.DateField(auto_now_add=True)
    is_paid = models.BooleanField(default=False)

    def __str__(self):
        return f"Invoice {self.invoice_number} - {self.amount} SAR"


class Refund(models.Model):

    class RefundStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        PROCESSED = 'processed', 'Processed'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='refunds')
    cancellation_request = models.ForeignKey(
        'drivers.DriverCancellationRequest', on_delete=models.CASCADE, null=True, blank=True
    )
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2)
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=RefundStatus.choices, default=RefundStatus.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Refund #{self.id} - {self.refund_amount} SAR - {self.status}"
