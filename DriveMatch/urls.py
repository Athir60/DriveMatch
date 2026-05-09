"""
URL configuration for DriveMatch project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings

from bookings import views as booking_views

urlpatterns = [
    path('admin/', admin.site.urls),

    path('', include('main.urls')),
    path('accounts/', include('accounts.urls')),
    path('drivers/', include('drivers.urls')),
    path('bookings/', include('bookings.urls')),
    path('support/', include('support.urls')),
    path('chat/', include('messaging.urls')),

    path('payments/callback/', booking_views.payment_callback, name='moyasar_payment_callback'),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)