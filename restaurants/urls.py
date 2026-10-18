from django.urls import path
from billing import views as billing_views
from menu import views as menu_views
from . import views

app_name = 'dashboard'

urlpatterns = [
    # Dashboard Home & Profile
    path('', views.dashboard_home, name='home'),
    path('profile/', views.dashboard_profile, name='profile'),
    path('toggle-status/', views.dashboard_toggle_status, name='toggle_status'),
    path('tables/', views.dashboard_tables, name='tables'),
    path('tables/<int:table_number>/qr/', views.table_qr_code, name='table_qr'),
    path('tables/print/', views.table_print_sheet, name='table_print'),

    # Menu Manager
    path('menu/', menu_views.menu_manager, name='menu'),
    path('menu/category/add/', menu_views.category_create, name='category_create'),
    path('menu/category/<int:pk>/edit/', menu_views.category_edit, name='category_edit'),
    path('menu/category/<int:pk>/delete/', menu_views.category_delete, name='category_delete'),
    path('menu/item/add/', menu_views.item_create, name='item_create'),
    path('menu/item/<int:pk>/edit/', menu_views.item_edit, name='item_edit'),
    path('menu/item/<int:pk>/delete/', menu_views.item_delete, name='item_delete'),
    path('menu/item/<int:pk>/toggle/', menu_views.item_toggle_availability, name='item_toggle'),

    # Subscription & Billing
    path('subscription/', billing_views.owner_subscription, name='subscription'),
    path('subscription/renew/', billing_views.owner_renew, name='subscription_renew'),
]
