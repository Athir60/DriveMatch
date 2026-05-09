from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('start/<int:driver_id>/', views.start_conversation, name='start_conversation'),
    path('thread/<int:thread_id>/', views.conversation, name='conversation'),
    path('my-messages/', views.passenger_threads, name='passenger_threads'),
    path('my-messages/', views.passenger_threads, name='passenger_message_list'),
    path('driver-messages/', views.driver_threads, name='driver_threads'),
    path('driver-messages/', views.driver_threads, name='driver_message_list'),
]
