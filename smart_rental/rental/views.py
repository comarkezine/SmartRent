from functools import wraps

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST
from django.db.models import Q
from .models import Tenant, Complaint
from .models import SystemActivity
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_http_methods
from django.db import transaction

from .forms import PropertyForm
from .models import Property, Tenant, Payment, Complaint, SystemActivity

from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import transaction
from django.shortcuts import render, redirect


from .models import Tenant, Payment, SystemActivity
from .mpesa import initiate_stk_push, MpesaError

import json
import logging

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone

from .ml_predictor import predict_rental_risk

from django.contrib.auth.decorators import user_passes_test

logger = logging.getLogger(__name__)

@csrf_exempt
@require_POST
def mpesa_callback(request):

    try:
        payload = json.loads(request.body)

        callback = payload["Body"]["stkCallback"]

        checkout_request_id = callback["CheckoutRequestID"]
        result_code = int(callback["ResultCode"])

    except (
        ValueError,
        KeyError,
        TypeError
    ):
        return JsonResponse(
            {"ResultCode": 1, "ResultDesc": "Invalid payload"},
            status=400
        )

    with transaction.atomic():

        payment = Payment.objects.select_for_update().filter(
            checkout_request_id=checkout_request_id
        ).first()

        if payment is None:
            logger.warning(
                "Unknown M-Pesa CheckoutRequestID received."
            )

            return JsonResponse(
                {"ResultCode": 1, "ResultDesc": "Unknown payment"},
                status=404
            )

        # Ignore duplicate callbacks for finalized payments.
        if payment.status in ("Completed", "Failed"):
            return JsonResponse(
                {"ResultCode": 0, "ResultDesc": "Already processed"}
            )

        if result_code == 0:

            metadata = callback.get(
                "CallbackMetadata",
                {}
            ).get("Item", [])

            values = {
                item.get("Name"): item.get("Value")
                for item in metadata
            }

            receipt = values.get("MpesaReceiptNumber")
            callback_amount = values.get("Amount")
            callback_phone = values.get("PhoneNumber")

            # Validate critical transaction information.
            try:
                received_amount = Decimal(
                    str(callback_amount)
                )
            except (InvalidOperation, TypeError):
                logger.warning(
                    "M-Pesa callback missing valid amount."
                )
                return JsonResponse(
                    {
                        "ResultCode": 1,
                        "ResultDesc": "Invalid payment amount"
                    },
                    status=400
                )

            if (
                not receipt
                or received_amount != payment.amount
                or str(callback_phone) != payment.phone_number
            ):
                logger.warning(
                    "M-Pesa callback payment details mismatch."
                )

                return JsonResponse(
                    {
                        "ResultCode": 1,
                        "ResultDesc": "Payment details mismatch"
                    },
                    status=400
                )

            payment.transaction_id = str(receipt)
            payment.status = "Completed"
            payment.paid_at = timezone.now()

            payment.save(
                update_fields=[
                    "transaction_id",
                    "status",
                    "paid_at"
                ]
            )

            SystemActivity.objects.create(
                user=payment.tenant.user,
                action="M-Pesa Payment Completed",
                description=f"Payment #{payment.id} completed."
            )

        else:

            payment.status = "Failed"
            payment.save(update_fields=["status"])

    return JsonResponse(
        {"ResultCode": 0, "ResultDesc": "Accepted"}
    )


# =====================================
# HOMEPAGE
# =====================================

def home(request):
    return render(request, "home.html")


# =====================================
# ROLE-BASED ACCESS CONTROL
# =====================================

def user_has_role(user, role_name):

    if not user.is_authenticated:
        return False

    # Superusers can access the System Admin Dashboard
    if role_name == "System Admin" and user.is_superuser:
        return True

    # Other users must belong to the correct group
    return user.groups.filter(name=role_name).exists()


def role_required(role_name):

    def decorator(view_func):

        @wraps(view_func)
        @login_required(login_url="home")
        def wrapper(request, *args, **kwargs):

            if user_has_role(request.user, role_name):
                return view_func(request, *args, **kwargs)

            raise PermissionDenied(
                f"You do not have permission to access the {role_name} dashboard."
            )

        return wrapper

    return decorator


# =====================================
# LOGIN FUNCTION
# =====================================

def role_login(request, role_name, template_name):

    if request.method == "POST":

        identifier = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        User = get_user_model()

        # Allow login using either email or username
        user_record = User.objects.filter(
            Q(email__iexact=identifier) |
            Q(username__iexact=identifier)
        ).first()

        if user_record:

            user = authenticate(
                request,
                username=user_record.get_username(),
                password=password
            )

            if user is not None:

                if user_has_role(user, role_name):

                    login(request, user)

                    dashboard_urls = {
                        "Tenant": "tenant_dashboard",
                        "Landlord": "landlord_dashboard",
                        "Property Manager": "manager_dashboard",
                        "System Admin": "admin_dashboard",
                    }

                    return redirect(
                        dashboard_urls[role_name]
                    )

        return render(
            request,
            template_name,
            {
                "login_error":
                "Invalid username, email, password, or account permissions."
            }
        )

    return render(request, template_name)


# =====================================
# LOGIN PAGES
# =====================================

def tenant_login(request):
    return role_login(
        request,
        "Tenant",
        "tenant_login.html"
    )


def landlord_login(request):
    return role_login(
        request,
        "Landlord",
        "landlord_login.html"
    )


def manager_login(request):
    return role_login(
        request,
        "Property Manager",
        "manager_login.html"
    )


def admin_login(request):
    return role_login(
        request,
        "System Admin",
        "admin_login.html"
    )


# =====================================
# TENANT DASHBOARD
# =====================================

@role_required("Tenant")
def tenant_dashboard(request):

    return render(
        request,
        "tenant_dashboard.html"
    )


# ============================================
# LANDLORD DASHBOARD
# ============================================

@role_required("Landlord")
def landlord_dashboard(request):

    # Retrieve properties belonging to this landlord
    properties = Property.objects.filter(
        landlord=request.user
    ).select_related(
        "property_manager"
    ).order_by("-created_at")

    # Retrieve complaints from those properties
    complaints = Complaint.objects.filter(
        tenant__property__landlord=request.user
    ).select_related(
        "tenant__user",
        "tenant__property"
    ).order_by("-created_at")

    # Retrieve payments from those properties
    payments = Payment.objects.filter(
        tenant__property__landlord=request.user
    ).select_related(
        "tenant__user",
        "tenant__property"
    ).order_by("-created_at")

    # Calculate payment statistics
    completed_payments = payments.filter(
        status="Completed"
    )

    pending_payments = payments.filter(
        status="Pending"
    )

    context = {

        # Property information
        "properties": properties,
        "total_properties": properties.count(),

        # Payment information
        "payments": payments,
        "payments_received": completed_payments.count(),
        "pending_payments": pending_payments.count(),

        # Complaint information
        "complaints": complaints,
        "open_complaints": complaints.exclude(
            status="Resolved"
        ).count(),

        # Predictive analytics (to be implemented later)
        "predictions": [],
    }

    return render(
        request,
        "landlord_dashboard.html",
        context
    )


# =====================================
# PROPERTY MANAGER DASHBOARD
# =====================================

@role_required("Property Manager")
def manager_dashboard(request):

    from .models import Property, Tenant, Payment, Complaint

    # Properties assigned to this manager
    properties = Property.objects.filter(
        property_manager=request.user
    )

    # Tenants living in those properties
    tenants = Tenant.objects.filter(
    property__property_manager=request.user,
    is_active=True
).select_related(
    "user",
    "property"
).order_by("user__username")

    # Payments made by those tenants
    payments = Payment.objects.filter(
        tenant__property__property_manager=request.user
    ).select_related(
        "tenant__user"
    ).order_by("-created_at")

    # Complaints submitted by those tenants
    complaints = Complaint.objects.filter(
        tenant__property__property_manager=request.user
    ).select_related(
        "tenant__user",
        "tenant__property"
    ).order_by("-created_at")

    context = {
        "properties": properties,
        "tenants": tenants,
        "payments": payments,
        "complaints": complaints,

        "total_properties": properties.count(),
        "total_tenants": tenants.count(),
        "total_payments": payments.count(),
        "open_complaints": complaints.exclude(
            status="Resolved"
        ).count(),
    }

    return render(
        request,
        "manager_dashboard.html",
        context
    )


# =====================================
# SYSTEM ADMIN DASHBOARD
# =====================================

@role_required("System Admin")
def admin_dashboard(request):

    User = get_user_model()

    users = User.objects.all().order_by("username")

    context = {
        "total_users": users.count(),
        "active_users": users.filter(is_active=True).count(),
        "inactive_users": users.filter(is_active=False).count(),
        "total_roles": Group.objects.count(),
        "users": users,
        "roles": Group.objects.all(),
        "activities": [],
    }

    return render(
        request,
        "admin_dashboard.html",
        context
    )


# =====================================
# LOGOUT
# =====================================

@require_POST
def logout_view(request):

    logout(request)

    return redirect("home")

# =====================================
# TENANT COMPLAINT SUBMISSION
# =====================================

@role_required("Tenant")
@require_POST
def submit_complaint(request):

    category = request.POST.get("category", "").strip()
    details = request.POST.get("details", "").strip()

    allowed_categories = [
        "Noise",
        "Garbage Collection",
        "Security",
        "Staff"
    ]

    if category not in allowed_categories or not details:
        return redirect("tenant_dashboard")

    # Find the tenant record associated with the logged-in user
    tenant = Tenant.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if tenant is None:
        return redirect("tenant_dashboard")

    # Save the complaint to the database
    Complaint.objects.create(
        tenant=tenant,
        category=category,
        description=details,
        status="Pending"
    )
    SystemActivity.objects.create(
    user=request.user,
    action="Complaint Submitted",
    description=f"Submitted a {category} complaint."
)

    return redirect("tenant_dashboard")


# =====================================
# M-PESA PAYMENT PAGE
# =====================================

@role_required("Tenant")
def mpesa_payment(request):

    tenant = Tenant.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if tenant is None:
        return render(
            request,
            "mpesa_payment.html",
            {
                "payment_error": (
                    "Your account is not linked "
                    "to an active tenancy."
                )
            }
        )

    payments = Payment.objects.filter(
        tenant=tenant
    ).order_by("-created_at")[:10]

    return render(
        request,
        "mpesa_payment.html",
        {
            "tenant": tenant,
            "payments": payments,
        }
    )
@role_required("Tenant")
@require_POST
def initiate_mpesa_payment(request):

    tenant = Tenant.objects.filter(
        user=request.user,
        is_active=True
    ).first()

    if tenant is None:
        return render(
            request,
            "mpesa_payment.html",
            {
                "payment_error": "Your account is not linked to an active tenancy."
            }
        )

    phone_number = request.POST.get("phone_number", "").strip()
    amount_input = request.POST.get("amount", "").strip()

    # Normalize Kenyan phone numbers
    cleaned_phone = phone_number.replace(" ", "").replace("-", "")

    if cleaned_phone.startswith("0") and len(cleaned_phone) == 10:
        cleaned_phone = "254" + cleaned_phone[1:]

    elif cleaned_phone.startswith("+254"):
        cleaned_phone = cleaned_phone[1:]

    # Validate phone number
    if not (
        cleaned_phone.isdigit()
        and len(cleaned_phone) == 12
        and cleaned_phone.startswith("254")
        and cleaned_phone[3] in ("1", "7")
    ):
        return render(
            request,
            "mpesa_payment.html",
            {
                "tenant": tenant,
                "payment_error": "Enter a valid Kenyan phone number."
            }
        )

    # Validate payment amount
    try:
        amount = Decimal(amount_input)

        if (
            not amount.is_finite()
            or amount <= 0
            or amount != amount.to_integral_value()
        ):
            raise InvalidOperation

    except (InvalidOperation, ValueError):
        return render(
            request,
            "mpesa_payment.html",
            {
                "tenant": tenant,
                "payment_error": "Enter a valid whole-number payment amount."
            }
        )

    # Create pending payment
    payment = Payment.objects.create(
        tenant=tenant,
        amount=amount,
        phone_number=cleaned_phone,
        status="Pending"
    )

    # Initiate M-Pesa STK Push
    try:
        response = initiate_stk_push(
            phone_number=cleaned_phone,
            amount=amount,
            account_reference=f"RENT{payment.id}"
        )

    except MpesaError as error:

        print("M-PESA ERROR:", str(error))

        payment.status = "Failed"
        payment.save(update_fields=["status"])

        return render(
            request,
            "mpesa_payment.html",
            {
                "tenant": tenant,
                "payment_error": (
                    "The payment request could not be initiated. "
                    "Please check your details and try again."
                )
            }
        )

    checkout_request_id = response.get("CheckoutRequestID")

    if not checkout_request_id:
        return render(
            request,
            "mpesa_payment.html",
            {
                "tenant": tenant,
                "payment_error": (
                    "Payment status is uncertain. "
                    "Check your payment history before trying again."
                )
            }
        )

    payment.checkout_request_id = checkout_request_id
    payment.save(update_fields=["checkout_request_id"])

    SystemActivity.objects.create(
        user=request.user,
        action="M-Pesa Payment Initiated",
        description=f"Payment request #{payment.id} submitted."
    )

    return redirect("mpesa_payment")



# =====================================
# PROPERTY REGISTRATION
# =====================================

@role_required("Landlord")
@require_http_methods(["GET", "POST"])
def register_property(request):

    if request.method == "POST":

        form = PropertyForm(request.POST)

        if form.is_valid():

            property_record = form.save(commit=False)

            # Automatically assign the logged-in landlord
            property_record.landlord = request.user

            property_record.save()

            # Record the activity
            SystemActivity.objects.create(
                user=request.user,
                action="Property Registered",
                description=(
                    f"Registered property: {property_record.name}"
                )
            )

            return redirect("landlord_dashboard")

    else:
        form = PropertyForm()

    return render(
        request,
        "register_property.html",
        {"form": form}
    )

    # ============================================
# LANDLORD - RESOLVE TENANT COMPLAINT
# ============================================

@role_required("Landlord")
@require_POST
def resolve_complaint(request, complaint_id):

    complaint = get_object_or_404(
        Complaint,
        id=complaint_id,
        tenant__property__landlord=request.user
    )

    with transaction.atomic():

        if complaint.status != "Resolved":

            complaint.status = "Resolved"
            complaint.save(update_fields=["status"])

            SystemActivity.objects.create(
                user=request.user,
                action="Complaint Resolved",
                description=(
                    f"Resolved complaint #{complaint.id} "
                    f"from {complaint.tenant.property.name}."
                )
            )

    return redirect("landlord_dashboard")


@login_required
def can_access_predictions(user):
    return (
        user.is_authenticated
        and (
            user.is_superuser
            or user.groups.filter(
                name__in=[
                    "Landlord",
                    "Property Manager",
                    "System Admin"
                ]
            ).exists()
        )
    )


@login_required
@user_passes_test(can_access_predictions, login_url="/")
def rental_risk_prediction(request):

    if request.method == "POST":
        try:
            income = int(request.POST.get("income"))
            expense_difficulty = int(
                request.POST.get("expense_difficulty")
            )
            household_size = int(
                request.POST.get("household_size")
            )

            if income not in range(1, 9):
                raise ValueError("Invalid income category.")

            if expense_difficulty not in range(1, 5):
                raise ValueError("Invalid expense difficulty category.")

            if household_size < 1:
                raise ValueError("Household size must be positive.")

            result = predict_rental_risk(
                income,
                expense_difficulty,
                household_size
            )

        except (TypeError, ValueError) as exc:
            error = str(exc)

    return render(
        request,
        "rental_risk_prediction.html",
        {
            "result": result,
            "error": error
        }
    )