from django.urls import path
from . import views

app_name = 'platform'

urlpatterns = [
    path('', views.platform_dashboard, name='dashboard'),
    path('restaurants/new/', views.platform_restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.platform_restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/toggle/', views.platform_toggle_restaurant, name='restaurant_toggle'),
    path('restaurants/<int:pk>/assist/', views.platform_impersonate, name='restaurant_assist'),
    path('billing/', views.platform_billing_overview, name='billing_overview'),
]
