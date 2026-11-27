from django.urls import path
from .views import (
    restaurant_menu,
    log_public_order,
    order_tracking,
    save_order_tip,
    order_upi_qr,
    check_order_status,
    submit_upi_payment,
    check_payment_status,
    order_receipt,
)

app_name = 'public'

urlpatterns = [
    path('r/<slug:slug>/', restaurant_menu, name='menu'),
    path('r/<slug:slug>/log-order/', log_public_order, name='log_order'),
    path('r/<slug:slug>/track/<int:order_id>/', order_tracking, name='order_tracking'),
    path('r/<slug:slug>/save-tip/', save_order_tip, name='save_order_tip'),
    path('r/<slug:slug>/upi-qr/<int:order_id>/', order_upi_qr, name='order_upi_qr'),
    path('r/<slug:slug>/order-status/<int:order_id>/', check_order_status, name='order_status'),
    path('r/<slug:slug>/pay-upi/', submit_upi_payment, name='submit_upi_payment'),
    path('r/<slug:slug>/payment-status/<int:order_id>/', check_payment_status, name='payment_status'),
    path('r/<slug:slug>/receipt/<int:order_id>/', order_receipt, name='receipt'),
]
