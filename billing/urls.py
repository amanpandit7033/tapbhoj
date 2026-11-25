from django.urls import path
from . import views

app_name = 'platform'

urlpatterns = [
    path('', views.platform_dashboard, name='dashboard'),
    path('dashboard/', views.platform_dashboard, name='today_dashboard'),
    path('today/', views.platform_dashboard, name='today'),
    path('overview/', views.platform_dashboard, name='overview'),
    path('stores/', views.platform_stores, name='stores'),
    path('restaurants/new/', views.platform_restaurant_create, name='restaurant_create'),
    path('restaurants/<int:pk>/', views.platform_restaurant_detail, name='restaurant_detail'),
    path('restaurants/<int:pk>/toggle/', views.platform_toggle_restaurant, name='restaurant_toggle'),
    path('restaurants/<int:pk>/impersonate/', views.platform_impersonate, name='restaurant_impersonate'),
    path('restaurants/<int:pk>/assist/', views.platform_impersonate, name='restaurant_assist'),
    path('impersonate/exit/', views.platform_exit_impersonate, name='exit_impersonate'),
    path('restaurants/<int:pk>/delete/', views.platform_restaurant_delete, name='restaurant_delete'),
    path('restaurants/<int:pk>/clear-orders/', views.platform_clear_test_orders, name='restaurant_clear_orders'),
    path('items/<int:pk>/toggle/', views.platform_item_toggle, name='item_toggle'),
    path('orders/', views.platform_live_orders, name='live_orders'),
    path('analytics/', views.platform_analytics, name='analytics'),
    path('subscriptions/', views.platform_subscriptions, name='subscriptions'),
    path('plans/', views.platform_plans, name='plans'),
    path('billing/', views.platform_billing_overview, name='billing_overview'),
    path('plans/new/', views.platform_plan_create, name='plan_create'),
    path('plans/<int:pk>/edit/', views.platform_plan_edit, name='plan_edit'),
    path('plans/<int:pk>/toggle/', views.platform_plan_toggle, name='plan_toggle'),
]

