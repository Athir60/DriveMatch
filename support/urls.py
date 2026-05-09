from django.urls import path
from . import views

app_name = 'support'

urlpatterns = [
    path('contact/', views.contact, name='contact'),
    path('tickets/', views.tickets, name='tickets'),
    path('tickets/new/', views.create_ticket, name='create_ticket'),
    path('complaint/<int:booking_id>/', views.create_complaint, name='create_complaint'),
]
