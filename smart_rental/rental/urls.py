from django.urls import path
from . import views

urlpatterns = [
    # Homepage
    path("", views.home, name="home"),

    # Login pages
    path("tenant/login/", views.tenant_login, name="tenant_login"),
    path("landlord/login/", views.landlord_login, name="landlord_login"),
    path("manager/login/", views.manager_login, name="manager_login"),
    path("system-admin/login/", views.admin_login, name="admin_login"),

    # Dashboards
    path("tenant/dashboard/", views.tenant_dashboard, name="tenant_dashboard"),
    path("landlord/dashboard/", views.landlord_dashboard, name="landlord_dashboard"),
    path("manager/dashboard/", views.manager_dashboard, name="manager_dashboard"),
    path("system-admin/dashboard/", views.admin_dashboard, name="admin_dashboard"),

    # Logout
    path("logout/", views.logout_view, name="logout"),


    # Tenant complaint submission
path(
    "tenant/submit-complaint/",
    views.submit_complaint,
    name="submit_complaint"
),

# M-Pesa payment page
path(
    "tenant/mpesa-payment/",
    views.mpesa_payment,
    name="mpesa_payment"
),
]