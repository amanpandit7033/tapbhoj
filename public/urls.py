from django.urls import path
from .views import (
    restaurant_menu,
    log_public_order,
    submit_upi_payment,
    check_payment_status,
    order_receipt,
)

app_name = 'public'

urlpatterns = [
    path('r/<slug:slug>/', restaurant_menu, name='menu'),
    path('r/<slug:slug>/log-order/', log_public_order, name='log_order'),
    path('r/<slug:slug>/pay-upi/', submit_upi_payment, name='submit_upi_payment'),
    path('r/<slug:slug>/payment-status/<int:order_id>/', check_payment_status, name='payment_status'),
    path('r/<slug:slug>/receipt/<int:order_id>/', order_receipt, name='receipt'),
]
