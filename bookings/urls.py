from django.urls import path
from . import views

app_name = 'bookings'

urlpatterns = [
    path('book/<int:driver_route_id>/', views.book_driver, name='book_driver'),
    path('payment/<int:payment_id>/', views.booking_payment, name='booking_payment'),
    path('payment/<int:payment_id>/confirm/', views.simulate_booking_payment_success, name='simulate_payment_success'),
    path('payment/<int:payment_id>/fail/', views.simulate_booking_payment_failed, name='simulate_payment_failed'),
    path('payment/callback/', views.payment_callback, name='payment_callback'),
    path('my-bookings/', views.my_bookings, name='my_bookings'),
    path('detail/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('contract/<int:contract_id>/', views.contract_detail, name='contract_detail'),
    path('rate/<int:booking_id>/', views.rate_driver, name='rate_driver'),
    path('invoices/', views.my_invoices, name='my_invoices'),
]
