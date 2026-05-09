from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/passenger/', views.passenger_register, name='passenger_register'),
    path('signin/', views.sign_in, name='sign_in'),
    path('signout/', views.sign_out, name='sign_out'),
    path('forgot-password/', views.forgot_password, name='forgot_password'),
    path('verify-reset-code/', views.verify_reset_code, name='verify_reset_code'),
    path('reset-password/', views.reset_password, name='reset_password'),
    path('forgot-username/', views.forgot_username, name='forgot_username'),
    path('profile/', views.passenger_profile, name='passenger_profile'),
    path('request-email-change/', views.request_email_change, name='request_email_change'),
    path('verify-email-otp/', views.verify_email_otp, name='verify_email_otp'),
    path('verify-registration/', views.verify_registration_otp, name='verify_registration_otp'),
]
