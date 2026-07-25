from django.urls import path
from .views import ActivateCodeView

urlpatterns = [
    path('activate/', ActivateCodeView.as_view(), name='premium_activate'),
]