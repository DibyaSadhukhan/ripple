from django.contrib import admin

from .models import EmailOTP


@admin.register(EmailOTP)
class EmailOTPAdmin(admin.ModelAdmin):
    list_display = [
        "email",
        "otp_code",
        "otp_token",
        "is_used",
        "created_at",
        "expires_at",
    ]

    list_filter = [
        "is_used",
        "created_at",
        "expires_at",
    ]

    search_fields = [
        "email",
        "otp_code",
        "otp_token",
    ]

    readonly_fields = [
        "created_at",
    ]