import base64
import requests

from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


class MpesaError(Exception):
    pass


def get_mpesa_base_url():

    if settings.MPESA_ENVIRONMENT == "sandbox":
        return "https://sandbox.safaricom.co.ke"

    if settings.MPESA_ENVIRONMENT == "production":
        return "https://api.safaricom.co.ke"

    raise ImproperlyConfigured(
        "Invalid MPESA_ENVIRONMENT setting."
    )


def get_access_token():

    if not (
        settings.MPESA_CONSUMER_KEY
        and settings.MPESA_CONSUMER_SECRET
    ):
        raise MpesaError(
            "M-Pesa consumer credentials are missing."
        )

    url = (
        f"{get_mpesa_base_url()}"
        "/oauth/v1/generate?grant_type=client_credentials"
    )

    try:
        response = requests.get(
            url,
            auth=(
                settings.MPESA_CONSUMER_KEY,
                settings.MPESA_CONSUMER_SECRET
            ),
            timeout=20
        )

        response.raise_for_status()

        return response.json()["access_token"]

    except (
        requests.RequestException,
        KeyError,
        ValueError
    ) as exc:

        raise MpesaError(
            "Unable to obtain M-Pesa access token."
        ) from exc


def initiate_stk_push(phone_number, amount, account_reference):

    required_settings = [
        settings.MPESA_SHORTCODE,
        settings.MPESA_PASSKEY,
        settings.MPESA_CALLBACK_URL,
    ]

    if not all(required_settings):
        raise MpesaError(
            "M-Pesa STK Push configuration is incomplete."
        )

    access_token = get_access_token()

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    password_string = (
        f"{settings.MPESA_SHORTCODE}"
        f"{settings.MPESA_PASSKEY}"
        f"{timestamp}"
    )

    password = base64.b64encode(
        password_string.encode("utf-8")
    ).decode("utf-8")

    url = (
        f"{get_mpesa_base_url()}"
        "/mpesa/stkpush/v1/processrequest"
    )

    payload = {
        "BusinessShortCode": settings.MPESA_SHORTCODE,
        "Password": password,
        "Timestamp": timestamp,
        "TransactionType": "CustomerPayBillOnline",
        "Amount": int(amount),
        "PartyA": phone_number,
        "PartyB": settings.MPESA_SHORTCODE,
        "PhoneNumber": phone_number,
        "CallBackURL": settings.MPESA_CALLBACK_URL,
        "AccountReference": account_reference,
        "TransactionDesc": "SmartRent Rent Payment",
    }

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    try:
        response = requests.post(
            url,
            json=payload,
            headers=headers,
            timeout=30
        )

        response.raise_for_status()

        data = response.json()

    except (
        requests.RequestException,
        ValueError
    ) as exc:

        raise MpesaError(
            "Unable to initiate M-Pesa payment."
        ) from exc

    if str(data.get("ResponseCode")) != "0":
        raise MpesaError(
            data.get(
                "ResponseDescription",
                "M-Pesa rejected the payment request."
            )
        )

    return data