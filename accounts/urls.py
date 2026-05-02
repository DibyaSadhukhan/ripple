from django.contrib.auth import views as auth_views
from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path("login/", views.request_otp_view, name="login"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path(
        "logout/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
]