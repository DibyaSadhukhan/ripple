import secrets
from random import randint
import hashlib
from django.conf import settings

from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.shortcuts import redirect, render
from django.utils import timezone
from .tasks import send_otp_email_task 
from .forms import EmailOTPRequestForm, EmailOTPVerifyForm
from .models import EmailOTP


User = get_user_model()


def generate_otp_code():
    return str(randint(100000, 999999))


def get_request_ip(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if forwarded_for:
        return forwarded_for.split(",")[0].strip()

    return request.META.get("REMOTE_ADDR", "unknown-ip")


def generate_otp_token(request, otp_code):
    now = timezone.now()
    request_ip = get_request_ip(request)

    raw_token = (
        f"otp-"
        f"{now.strftime('%d-%m-%Y-%H-%M-%S')}-"
        f"{settings.OTP_SECRET}-"
        f"{request_ip}-"
        f"{otp_code}"
    )

    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_internal_username(email):
    email_prefix = email.split("@")[0]
    cleaned_prefix = "".join(
        character for character in email_prefix if character.isalnum()
    )

    if not cleaned_prefix:
        cleaned_prefix = "user"

    base_username = cleaned_prefix.lower()
    username = base_username
    counter = 1

    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1

    return username

def request_otp_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    if request.method == "POST":
        form = EmailOTPRequestForm(request.POST)

        if form.is_valid():
            email = form.cleaned_data["email"].lower()
            otp_code = generate_otp_code()
            otp_token = generate_otp_token(request, otp_code)

            EmailOTP.objects.create(
                email=email,
                otp_code=otp_code,
                otp_token=otp_token,
            )

            send_otp_email_task.delay(email, otp_code)

            request.session["otp_token"] = otp_token
            request.session["otp_email"] = email

            messages.success(request, "OTP sent to your email address.")
            return redirect("accounts:verify_otp")
    else:
        form = EmailOTPRequestForm()

    return render(request, "accounts/request_otp.html", {"form": form})


def verify_otp_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:home")

    otp_token = request.session.get("otp_token")
    otp_email = request.session.get("otp_email")

    if not otp_token or not otp_email:
        messages.error(request, "Please request a new OTP.")
        return redirect("accounts:login")

    if request.method == "POST":
        form = EmailOTPVerifyForm(request.POST)

        if form.is_valid():
            otp_code = form.cleaned_data["otp_code"]

            otp_record = EmailOTP.objects.filter(
                email=otp_email,
                otp_token=otp_token,
                otp_code=otp_code,
                is_used=False,
            ).first()

            if not otp_record:
                messages.error(request, "Invalid OTP.")
                return redirect("accounts:verify_otp")

            if otp_record.is_expired():
                messages.error(request, "OTP has expired. Please request a new OTP.")
                return redirect("accounts:login")

            user = User.objects.filter(email=otp_email).first()

            if not user:
                user = User.objects.create(
                    username=generate_internal_username(otp_email),
                    email=otp_email,
                )
                user.set_unusable_password()
                user.save()

            otp_record.is_used = True
            otp_record.save()

            request.session.pop("otp_token", None)
            request.session.pop("otp_email", None)

            login(request, user)

            messages.success(request, "You are now logged in.")
            return redirect("dashboard:home")
    else:
        form = EmailOTPVerifyForm()

    return render(request, "accounts/verify_otp.html", {"form": form})