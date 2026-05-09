from django.db import models
from django.contrib.auth.models import User



class SubscriptionPlan(models.Model):
    """Plans available for drivers to subscribe to the platform."""
    name = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=8, decimal_places=2)
    duration_days = models.IntegerField()
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price} SAR"



class DriverProfile(models.Model):

    class VerificationStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    national_id = models.CharField(max_length=50, blank=True)
    id_front = models.ImageField(upload_to='documents/id/', blank=True, null=True)
    id_back = models.ImageField(upload_to='documents/id/', blank=True, null=True)
    driver_license = models.ImageField(upload_to='documents/license/', blank=True, null=True)

    verification_status = models.CharField(
        max_length=20,
        choices=VerificationStatus.choices,
        default=VerificationStatus.PENDING
    )

    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_trips = models.IntegerField(default=0)
    bio = models.TextField(blank=True)
    profile_photo = models.ImageField(upload_to="images/drivers/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        full = self.user.get_full_name()
        name = full if full else self.user.username
        return f"Driver: {name} ({self.verification_status})"

    def is_verified(self):
        return self.verification_status == self.VerificationStatus.APPROVED



class Vehicle(models.Model):

    class CarType(models.TextChoices):
        SEDAN = 'sedan', 'Sedan'
        SUV = 'suv', 'SUV'
        HATCHBACK = 'hatchback', 'Hatchback'
        COUPE = 'coupe', 'Coupe'
        CONVERTIBLE = 'convertible', 'Convertible'
        WAGON = 'wagon', 'Wagon'
        MINIVAN = 'minivan', 'Minivan'
        VAN = 'van', 'Van'
        PICKUP = 'pickup', 'Pickup'
        CROSSOVER = 'crossover', 'Crossover'
        LUXURY = 'luxury', 'Luxury'
        ELECTRIC = 'electric', 'Electric'
        HYBRID = 'hybrid', 'Hybrid'
        BUS = 'bus', 'Bus'
        OTHER = 'other', 'Other'

    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE)
    brand = models.CharField(max_length=100)
    model = models.CharField(max_length=100)
    year = models.IntegerField()
    color = models.CharField(max_length=50)
    license_plate = models.CharField(max_length=20, unique=True)
    car_type = models.CharField(max_length=20, choices=CarType.choices, default=CarType.SEDAN)
    car_photo = models.ImageField(upload_to='images/cars/', blank=True, null=True)

    def __str__(self):
        return f"{self.year} {self.brand} {self.model} - {self.color} ({self.license_plate})"



class Route(models.Model):
    from_area = models.CharField(max_length=100)
    to_area = models.CharField(max_length=100)
    city = models.CharField(max_length=100, default='Riyadh')

    def __str__(self):
        return f"{self.from_area} → {self.to_area}"

    class Meta:
        unique_together = ('from_area', 'to_area', 'city')



class DriverRoute(models.Model):

    class CommitmentDuration(models.TextChoices):
        ONE_MONTH = '1', '1 Month'
        TWO_MONTHS = '2', '2 Months'
        THREE_MONTHS = '3', '3 Months'
        SIX_MONTHS = '6', '6 Months'
        TWELVE_MONTHS = '12', '12 Months'

    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='routes')
    route = models.ForeignKey(Route, on_delete=models.PROTECT)
    available_days = models.CharField(max_length=100)
    start_time = models.TimeField()
    end_time = models.TimeField()
    monthly_price = models.DecimalField(max_digits=8, decimal_places=2)

    commitment_duration = models.CharField(
        max_length=5,
        choices=CommitmentDuration.choices,
        default=CommitmentDuration.ONE_MONTH
    )

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.driver} | {self.route} | {self.monthly_price} SAR/month"

    def get_days_list(self):
        return self.available_days.split(',') if self.available_days else []



class DriverSubscription(models.Model):
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} - {self.plan.name}"



class FavoriteDriver(models.Model):
    passenger = models.ForeignKey('accounts.PassengerProfile', on_delete=models.CASCADE, related_name='favorites')
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('passenger', 'driver')

    def __str__(self):
        return f"{self.passenger} - {self.driver}"



class DriverCancellationRequest(models.Model):

    class RequestStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'

    booking = models.ForeignKey('bookings.Booking', on_delete=models.CASCADE, related_name='cancellation_requests')
    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=RequestStatus.choices, default=RequestStatus.PENDING)
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    admin_notes = models.TextField(blank=True)

    def __str__(self):
        return f"Cancellation Request #{self.id} - {self.driver} - {self.status}"



class DriverBankAccount(models.Model):
    """
    Driver's bank account details for receiving payouts.
    One bank account per driver (OneToOneField).
    """
    driver = models.OneToOneField(DriverProfile, on_delete=models.CASCADE, related_name='bank_account')
    bank_name = models.CharField(max_length=100)
    iban = models.CharField(max_length=34)
    account_holder_name = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.driver} — {self.bank_name} ({self.iban[-4:]})"



class DriverSubscriptionPayment(models.Model):

    class PaymentStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        PAID = 'paid', 'Paid'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'

    driver = models.ForeignKey(DriverProfile, on_delete=models.CASCADE, related_name='subscription_payments')
    subscription = models.OneToOneField(
        DriverSubscription, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='payment'
    )
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    payment_reference = models.CharField(max_length=100, blank=True)
    card_last4 = models.CharField(max_length=4, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"DriverPayment #{self.id} - {self.driver} - {self.amount} SAR - {self.status}"
