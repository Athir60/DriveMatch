from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    path('', views.landing, name='landing'),
    path('home/', views.passenger_home, name='passenger_home'),
    path('contact/', views.contact, name='contact'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('about/', views.about, name='about'),
    path('careers/', views.careers, name='careers'),
    path('more/', views.passenger_more, name='passenger_more'),
    path('messages/', views.passenger_messages_redirect, name='passenger_messages'),
]
