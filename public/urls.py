from django.urls import path
from .views import restaurant_menu, log_public_order

app_name = 'public'

urlpatterns = [
    path('r/<slug:slug>/', restaurant_menu, name='menu'),
    path('r/<slug:slug>/log-order/', log_public_order, name='log_order'),
]
