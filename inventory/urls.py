from django.urls import path
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # Auth (using our template)
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),

    # Pages
    path('admin-page/', views.admin_page, name='admin_page'),
    path('inventory/', views.inventory_page, name='inventory_page'),
    path('edit/<int:tyre_id>/', views.edit_tyre, name='edit_tyre'),
    path('sell/<int:tyre_id>/<str:shop_code>/', views.sell_tyre, name='sell_tyre'),
    path('sales-log/', views.sale_log, name='sale_log'),
        path("admin/inventory/", views.admin_inventory, name="admin_inventory"),
    path("admin/inventory/delete/<int:tyre_id>/", views.delete_tyre, name="delete_tyre"),
]

# Default route → login (or change to inventory_page if you prefer)
urlpatterns += [
    path('', lambda request: redirect('login')),
]
