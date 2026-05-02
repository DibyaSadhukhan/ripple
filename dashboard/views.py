from django.contrib.auth.decorators import login_required
from django.shortcuts import render


@login_required
def home(request):
    context = {
        "page_title": "Ripple Dashboard",
    }

    return render(request, "dashboard/home.html", context)