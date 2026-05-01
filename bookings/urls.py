from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('payment/<str:booking_id>/', views.payment,name='payment'),
    path('booking-success/<str:booking_id>/', views.booking_success, name='booking_success'),
    path('admin-login/',views.admin_login, name='admin_login'),
    path('admin-logout/',  views.admin_logout,name='admin_logout'),
    path('admin-dashboard/',views.admin_dashboard, name='admin_dashboard'),
    path('export-month/',views.export_month,name='export_month'),
    path('api/slot-fee/',views.get_slot_fee, name='get_slot_fee'),
    path('api/booked-slots/', views.get_booked_slots,name='get_booked_slots'),
]