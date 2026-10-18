from django.urls import path
from .views import restaurant_menu

app_name = 'public'

urlpatterns = [
    path('r/<slug:slug>/', restaurant_menu, name='menu'),
]
