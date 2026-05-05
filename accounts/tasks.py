from celery import shared_task
from django.core.mail import send_mail


@shared_task
def send_otp_email_task(email, otp_code):
    send_mail(
        subject="Your Ripple login OTP",
        message=f"Your Ripple login OTP is {otp_code}. This code will expire in 15 Minutes.",
        from_email=None,
        recipient_list=[email],
        fail_silently=False,
    )