from functools import wraps

from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.views.decorators.http import require_POST


# =====================================
# HOMEPAGE
# =====================================

def home(request):
    return render(request, "home.html")


# =====================================
# ROLE-BASED ACCESS CONTROL
# =====================================

def role_required(role_name):

    def decorator(view_func):

        @wraps(view_func)
        @login_required(login_url="home")
        def wrapper(request, *args, **kwargs):

            user = request.user



            if (
    (role_name == "System Admin" and user.is_superuser)
    or user.groups.filter(name=role_name).exists()
):


  
                return view_func(request, *args, **kwargs)

            raise PermissionDenied(
                "You do not have permission to access this dashboard."
            )

        return wrapper

    return decorator


# =====================================
# LOGIN FUNCTION
# =====================================

def role_login(request, role_name, template_name):

    if request.method == "POST":

        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")

        User = get_user_model()

        user_record = User.objects.filter(
            email__iexact=email
        ).first()

        if user_record:

            user = authenticate(
                request,
                username=user_record.get_username(),
                password=password
            )

            if user is not None:

                if (
    (role_name == "System Admin" and user.is_superuser)
    or user.groups.filter(name=role_name).exists()
):

                    login(request, user)

                    if role_name == "Tenant":
                        return redirect("tenant_dashboard")

                    elif role_name == "Landlord":
                        return redirect("landlord_dashboard")

                    elif role_name == "Property Manager":
                        return redirect("manager_dashboard")

                    elif role_name == "System Admin":
                        return redirect("admin_dashboard")

        return render(
    request,
    template_name,
    {
        "login_error": "Invalid email, password, or account permissions."
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


# =====================================
# LANDLORD DASHBOARD
# =====================================

@role_required("Landlord")
def landlord_dashboard(request):
    return render(
        request,
        "landlord_dashboard.html"
    )


# =====================================
# PROPERTY MANAGER DASHBOARD
# =====================================

@role_required("Property Manager")
def manager_dashboard(request):
    return render(
        request,
        "manager_dashboard.html"
    )


# =====================================
# SYSTEM ADMIN DASHBOARD
# =====================================

@role_required("System Admin")
def admin_dashboard(request):
    return render(
        request,
        "admin_dashboard.html"
    )


# =====================================
# LOGOUT
# =====================================

def logout_view(request):

    logout(request)

    return redirect("home")

    from django.views.decorators.http import require_POST


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

    # Complaint database storage will be added next.
    # For now, this confirms that the form reaches Django.

    return redirect("tenant_dashboard")


# =====================================
# M-PESA PAYMENT PAGE
# =====================================

@role_required("Tenant")
def mpesa_payment(request):

    return render(
        request,
        "mpesa_payment.html"
    )