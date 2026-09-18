
# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings


# =======================================================================================================
# Admin
# =======================================================================================================

class Admin(models.Model):

    # ==============================
    # CHOICES
    # ==============================

    ROLE_CHOICES = [
        ('ADMIN', 'Admin'),
        ('SUPER_ADMIN', 'Super Admin'),
    ]

    # ==============================
    # BASIC INFORMATION
    # ==============================

    first_name = models.CharField(
        max_length=50
    )

    last_name = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    email = models.EmailField(
        max_length=30,
        unique=True
    )

    password = models.CharField(
        max_length=255
    )

    contact = models.CharField(
        max_length=15,
        unique=True
    )

    # ==============================
    # ADMIN ROLE
    # ==============================

    role = models.CharField(
        max_length=15,
        choices=ROLE_CHOICES
    )

    # ==============================
    # ACCOUNT STATUS
    # ==============================

    is_active = models.BooleanField(
        default=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'admins'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.email


# =======================================================================================================
# User
# =======================================================================================================

class User(AbstractUser):

    # ==============================
    # CHOICES
    # ==============================

    ROLE_CHOICES = [
        ('FOOD_BUSINESS', 'Food Business'),
        ('NGO', 'NGO'),
        ('CUSTOMER', 'Customer'),
        ('VOLUNTEER', 'Volunteer'),
    ]

    # ==============================
    # REMOVE DEFAULT USER FIELDS
    # ==============================

    username = None
    first_name = None
    last_name = None

    # ==============================
    # BASIC INFORMATION
    # ==============================

    first_name = models.CharField(
        max_length=50
    )

    last_name = models.CharField(
        max_length=50,
        null=True,
        blank=True
    )

    email = models.EmailField(
        max_length=30,
        unique=True
    )

    contact = models.CharField(
        max_length=15,
        unique=True
    )

    # ==============================
    # USER ROLE
    # ==============================

    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES
    )

    # ==============================
    # ACCOUNT STATUS
    # ==============================

    is_active = models.BooleanField(
        default=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    # ==============================
    # LOGIN SETTINGS
    # ==============================

    USERNAME_FIELD = 'email'

    REQUIRED_FIELDS = ['first_name']

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'users'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.email


# =======================================================================================================
# Food Business
# =======================================================================================================

class FoodBusiness(models.Model):

    # ==============================
    # USER RELATIONSHIP
    # ==============================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='food_business'
    )

    # ==============================
    # BUSINESS INFORMATION
    # ==============================

    business_name = models.CharField(
        max_length=50
    )

    business_type = models.CharField(
        max_length=40
    )

    contact_person = models.CharField(
        max_length=80
    )

    contact = models.CharField(
        max_length=15
    )

    # ==============================
    # LOCATION INFORMATION
    # ==============================

    address = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=50
    )

    pincode = models.CharField(
        max_length=10
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'food_businesses'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.business_name


# =======================================================================================================
# NGO
# =======================================================================================================

class NGO(models.Model):

    # ==============================
    # USER RELATIONSHIP
    # ==============================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='ngo'
    )

    # ==============================
    # ORGANIZATION INFORMATION
    # ==============================

    organization_name = models.CharField(
        max_length=50
    )

    receiver_type = models.CharField(
        max_length=20
    )

    contact_person = models.CharField(
        max_length=80
    )

    contact = models.CharField(
        max_length=15
    )

    # ==============================
    # LOCATION INFORMATION
    # ==============================

    address = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=50
    )

    pincode = models.CharField(
        max_length=10
    )

    # ==============================
    # CAPACITY & REQUIREMENTS
    # ==============================

    capacity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    requirements = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'ngos'

        constraints = [
            models.CheckConstraint(
                check=models.Q(capacity__gt=0),
                name='ngo_capacity_gt_0'
            )
        ]

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.organization_name


# =======================================================================================================
# Customer
# =======================================================================================================

class Customer(models.Model):

    # ==============================
    # USER RELATIONSHIP
    # ==============================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='customer'
    )

    # ==============================
    # LOCATION INFORMATION
    # ==============================

    address = models.CharField(
        max_length=100
    )

    city = models.CharField(
        max_length=50
    )

    pincode = models.CharField(
        max_length=10
    )

    # ==============================
    # PREFERENCES
    # ==============================

    food_preferences = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'customers'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"Customer #{self.pk}"


# =======================================================================================================
# Volunteer
# =======================================================================================================

class Volunteer(models.Model):

    # ==============================
    # USER RELATIONSHIP
    # ==============================

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='volunteer'
    )

    # ==============================
    # VOLUNTEER INFORMATION
    # ==============================

    vehicle_type = models.CharField(
        max_length=30,
        null=True,
        blank=True
    )

    availability_status = models.CharField(
        max_length=15,
        default='AVAILABLE'
    )

    service_area = models.CharField(
        max_length=100,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'volunteers'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"Volunteer #{self.pk}"


# =======================================================================================================
# Food Item
# =======================================================================================================

class FoodItem(models.Model):

    # ==============================
    # CHOICES
    # ==============================

    DESTINATION_TYPE_CHOICES = [
        ('SALE', 'Sale'),
        ('DONATION', 'Donation'),
        ('COMMUNITY', 'Community'),
        ('DISPOSAL', 'Disposal'),
    ]

    # ==============================
    # PROVIDER RELATIONSHIP
    # ==============================

    provider = models.ForeignKey(
        'FoodBusiness',
        on_delete=models.CASCADE,
        related_name='food_items'
    )

    # ==============================
    # BASIC FOOD INFORMATION
    # ==============================

    food_name = models.CharField(
        max_length=100
    )

    category = models.CharField(
        max_length=40
    )

    quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    unit = models.CharField(
        max_length=15
    )

    # ==============================
    # FOOD TIMING
    # ==============================

    preparation_time = models.DateTimeField()

    expiry_time = models.DateTimeField()

    # ==============================
    # FOOD CONDITION & DESTINATION
    # ==============================

    condition = models.CharField(
        max_length=50
    )

    destination_type = models.CharField(
        max_length=15,
        choices=DESTINATION_TYPE_CHOICES,
        null=True,
        blank=True
    )

    # ==============================
    # FOOD STATUS
    # ==============================

    status = models.CharField(
        max_length=15,
        default='AVAILABLE'
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'food_items'

        constraints = [
            models.CheckConstraint(
                check=models.Q(quantity__gt=0),
                name='food_item_quantity_gt_0'
            ),
            models.CheckConstraint(
                check=models.Q(expiry_time__gt=models.F('preparation_time')),
                name='food_item_expiry_after_preparation'
            )
        ]

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.food_name


# =======================================================================================================
# Food Eligibility
# =======================================================================================================

class FoodEligibility(models.Model):

    # ==============================
    # CHOICES
    # ==============================

    ELIGIBILITY_STATUS_CHOICES = [
        ('SALE', 'Sale'),
        ('DONATION', 'Donation'),
        ('COMMUNITY', 'Community'),
        ('DISPOSAL', 'Disposal'),
    ]

    # ==============================
    # FOOD RELATIONSHIP
    # ==============================

    food = models.OneToOneField(
        'FoodItem',
        on_delete=models.CASCADE,
        related_name='eligibility'
    )

    # ==============================
    # ELIGIBILITY DETAILS
    # ==============================

    is_eligible = models.BooleanField()

    eligibility_status = models.CharField(
        max_length=15,
        choices=ELIGIBILITY_STATUS_CHOICES
    )

    reason = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    checked_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'food_eligibility'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"{self.food.food_name} - {self.eligibility_status}"


# =======================================================================================================
# Food Request
# =======================================================================================================

class FoodRequest(models.Model):

    # ==============================
    # CHOICES
    # ==============================

    REQUEST_TYPE_CHOICES = [
        ('PURCHASE', 'Purchase'),
        ('DONATION', 'Donation'),
    ]

    # ==============================
    # RELATIONSHIPS
    # ==============================

    food = models.ForeignKey(
        'FoodItem',
        on_delete=models.CASCADE,
        related_name='requests'
    )

    requester_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='food_requests'
    )

    # ==============================
    # REQUEST DETAILS
    # ==============================

    requested_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    request_type = models.CharField(
        max_length=15,
        choices=REQUEST_TYPE_CHOICES
    )

    # ==============================
    # REQUEST STATUS
    # ==============================

    status = models.CharField(
        max_length=15,
        default='PENDING'
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    requested_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'food_requests'

        constraints = [
            models.CheckConstraint(
                check=models.Q(requested_quantity__gt=0),
                name='food_request_quantity_gt_0'
            )
        ]

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"{self.requester_user} - {self.food.food_name}"


# =======================================================================================================
# Match
# =======================================================================================================

class Match(models.Model):

    # ==============================
    # CHOICES
    # ==============================

    STATUS_CHOICES = [
        ('PROPOSED', 'Proposed'),
        ('ACCEPTED', 'Accepted'),
        ('REJECTED', 'Rejected'),
        ('COMPLETED', 'Completed'),
    ]

    # ==============================
    # RELATIONSHIPS
    # ==============================

    food = models.ForeignKey(
        'FoodItem',
        on_delete=models.CASCADE,
        related_name='matches'
    )

    receiver_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='matches_received'
    )

    # ==============================
    # MATCH DETAILS
    # ==============================

    distance_km = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        null=True,
        blank=True
    )

    matched_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    match_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    # ==============================
    # MATCH STATUS
    # ==============================

    status = models.CharField(
        max_length=15,
        choices=STATUS_CHOICES,
        default='PROPOSED'
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    matched_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'matches'

        constraints = [
            models.CheckConstraint(
                check=models.Q(distance_km__gte=0),
                name='match_distance_gte_0'
            ),
            models.CheckConstraint(
                check=models.Q(matched_quantity__gt=0),
                name='match_quantity_gt_0'
            )
        ]

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"{self.food.food_name} -> {self.receiver_user}"


# =======================================================================================================
# Pickup
# =======================================================================================================

class Pickup(models.Model):

    # ==============================
    # RELATIONSHIPS
    # ==============================

    food = models.ForeignKey(
        'FoodItem',
        on_delete=models.CASCADE,
        related_name='pickups'
    )

    volunteer = models.ForeignKey(
        'Volunteer',
        on_delete=models.CASCADE,
        related_name='pickups'
    )

    # ==============================
    # PICKUP DETAILS
    # ==============================

    pickup_time = models.DateTimeField()

    status = models.CharField(
        max_length=15,
        default='ASSIGNED'
    )

    otp_code = models.CharField(
        max_length=6,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'pickups'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"{self.food.food_name} - {self.volunteer}"


# =======================================================================================================
# Delivery
# =======================================================================================================

class Delivery(models.Model):

    # ==============================
    # RELATIONSHIPS
    # ==============================

    pickup = models.ForeignKey(
        'Pickup',
        on_delete=models.CASCADE,
        related_name='deliveries'
    )

    receiver_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='deliveries_received'
    )

    # ==============================
    # DELIVERY DETAILS
    # ==============================

    delivery_time = models.DateTimeField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=15,
        default='IN_TRANSIT'
    )

    verification_code = models.CharField(
        max_length=20,
        null=True,
        blank=True
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'deliveries'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"Delivery #{self.pk} - {self.receiver_user}"


# =======================================================================================================
# Notification
# =======================================================================================================

class Notification(models.Model):

    # ==============================
    # USER RELATIONSHIP
    # ==============================

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    # ==============================
    # NOTIFICATION CONTENT
    # ==============================

    title = models.CharField(
        max_length=100
    )

    message = models.CharField(
        max_length=500
    )

    notification_type = models.CharField(
        max_length=30
    )

    # ==============================
    # NOTIFICATION STATUS
    # ==============================

    is_read = models.BooleanField(
        default=False
    )

    # ==============================
    # TIMESTAMPS
    # ==============================

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'notifications'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return self.title


# =======================================================================================================
# Analytics
# =======================================================================================================

class Analytics(models.Model):

    # ==============================
    # FOOD RELATIONSHIP
    # ==============================

    food = models.ForeignKey(
        'FoodItem',
        on_delete=models.CASCADE,
        related_name='analytics_records'
    )

    # ==============================
    # QUANTITY BREAKDOWN
    # ==============================

    prepared_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    sold_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    donated_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    rescued_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    wasted_quantity = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    # ==============================
    # RECORD DETAILS
    # ==============================

    record_date = models.DateField()

    remarks = models.CharField(
        max_length=300,
        null=True,
        blank=True
    )

    # ==============================
    # DATABASE TABLE
    # ==============================

    class Meta:
        db_table = 'analytics'

    # ==============================
    # STRING REPRESENTATION
    # ==============================

    def __str__(self):
        return f"{self.food.food_name} - {self.record_date}"