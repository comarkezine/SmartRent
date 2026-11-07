from django.contrib import admin

from .models import (
    Property,
    Tenant,
    Payment,
    Complaint,
    SystemActivity
)


@admin.register(Property)
class PropertyAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "location",
        "landlord",
        "property_manager",
        "status"
    )

    search_fields = (
        "name",
        "location"
    )


@admin.register(Tenant)
class TenantAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "property",
        "unit_number",
        "monthly_rent",
        "is_active"
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "tenant",
        "amount",
        "phone_number",
        "status",
        "transaction_id",
        "created_at",
    )

    list_filter = (
        "status",
        "created_at",
    )

    search_fields = (
        "tenant__user__username",
        "tenant__property__name",
        "transaction_id",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
    )


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):

    list_display = (
        "tenant",
        "category",
        "status",
        "created_at"
    )

    list_filter = (
        "category",
        "status"
    )


@admin.register(SystemActivity)
class SystemActivityAdmin(admin.ModelAdmin):

    list_display = (
        "user",
        "action",
        "created_at"
    )