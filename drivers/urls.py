from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path('register/step1/', views.driver_register_step1, name='driver_register_step1'),
    path('register/step2/', views.driver_register_step2, name='driver_register_step2'),
    path('register/step3/', views.driver_register_step3, name='driver_register_step3'),
    path('register/step4/', views.driver_register_step4, name='driver_register_step4'),
    path('register/step5/', views.driver_register_step5, name='driver_register_step5'),
    path('register/step6/', views.driver_register_step6, name='driver_register_step6'),
    path('register/step7/', views.driver_register_step7, name='driver_register_step7'),

    path('dashboard/', views.driver_dashboard, name='driver_dashboard'),
    path('trips/', views.driver_trips, name='driver_trips'),
    path('trips-table/', views.trips_table, name='trips_table'),
    path('subscribers/', views.subscribers, name='subscribers'),
    path('earnings/', views.earnings, name='earnings'),
    path('ratings/', views.driver_ratings, name='driver_ratings'),
    path('complaints/', views.driver_complaints, name='driver_complaints'),
    path('settings/', views.driver_settings, name='driver_settings'),
    path('cancellation/<int:booking_id>/', views.submit_cancellation_request, name='submit_cancellation_request'),

    path('service-settings/', views.service_settings, name='service_settings'),
    path('service-settings/add-route/', views.add_driver_route, name='add_driver_route'),
    path('service-settings/edit-route/<int:route_id>/', views.edit_driver_route, name='edit_driver_route'),
    path('service-settings/deactivate-route/<int:route_id>/', views.deactivate_driver_route, name='deactivate_driver_route'),

    path('subscription-payment/<int:payment_id>/', views.driver_subscription_payment, name='driver_subscription_payment'),
    path('subscription-payment/<int:payment_id>/confirm/', views.simulate_subscription_payment_success, name='simulate_sub_payment_success'),
    path('subscription-payment/<int:payment_id>/fail/', views.simulate_subscription_payment_failed, name='simulate_sub_payment_failed'),
    path('subscription-payment/<int:payment_id>/moyasar-callback/', views.moyasar_payment_callback, name='moyasar_payment_callback'),

    path('more/', views.driver_more, name='driver_more'),
    path('profile-page/', views.driver_profile_page, name='driver_profile_page'),
    path('messages/', views.driver_messages, name='driver_messages'),
    path('tickets/', views.driver_tickets, name='driver_tickets'),
    path('subscription/', views.driver_subscription, name='driver_subscription'),
    path('driver-invoices/', views.driver_invoices, name='driver_invoices'),
    path('privacy/', views.driver_privacy, name='driver_privacy'),

    path('search/', views.search_drivers, name='search_drivers'),
    path('profile/<int:driver_id>/', views.driver_profile_view, name='driver_profile_view'),
    path('favorite/<int:driver_id>/', views.toggle_favorite, name='toggle_favorite'),
    path('favorites/', views.my_favorites, name='my_favorites'),
]
