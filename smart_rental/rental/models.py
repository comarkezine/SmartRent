from django.db import models
from django.conf import settings


# =====================================
# PROPERTY MODEL
# =====================================

class Property(models.Model):

    STATUS_CHOICES = [
        ("Available", "Available"),
        ("Occupied", "Occupied"),
        ("Maintenance", "Maintenance"),
    ]

    name = models.CharField(max_length=150)

    location = models.CharField(max_length=200)

    units = models.PositiveIntegerField(default=1)

    landlord = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="owned_properties"
    )

    property_manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_properties"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Available"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


# =====================================
# TENANT MODEL
# =====================================

class Tenant(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tenant_profile"
    )

    property = models.ForeignKey(
        Property,
        on_delete=models.PROTECT,
        related_name="tenants"
    )

    unit_number = models.CharField(max_length=30)

    phone_number = models.CharField(max_length=15)

    monthly_rent = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    lease_start = models.DateField()

    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.user.get_username()


# =====================================
# PAYMENT MODEL
# =====================================

class Payment(models.Model):

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Completed", "Completed"),
        ("Failed", "Failed"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="payments"
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    phone_number = models.CharField(max_length=15)

    transaction_id = models.CharField(
        max_length=100,
        unique=True,
        null=True,
        blank=True
    )

    checkout_request_id = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    paid_at = models.DateTimeField(
        null=True,
        blank=True
    )

    def __str__(self):
        return f"{self.tenant} - KES {self.amount} - {self.status}"


# =====================================
# COMPLAINT MODEL
# =====================================

class Complaint(models.Model):

    CATEGORY_CHOICES = [
        ("Noise", "Noise"),
        ("Garbage Collection", "Garbage Collection"),
        ("Security", "Security"),
        ("Staff", "Staff"),
    ]

    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("In Progress", "In Progress"),
        ("Resolved", "Resolved"),
    ]

    tenant = models.ForeignKey(
        Tenant,
        on_delete=models.PROTECT,
        related_name="complaints"
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES
    )

    description = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="Pending"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tenant} - {self.category}"


# =====================================
# SYSTEM ACTIVITY MODEL
# =====================================

class SystemActivity(models.Model):

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    action = models.CharField(max_length=200)

    description = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.action