from django.contrib import admin
from .models import PassengerProfile


class PassengerProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'phone_number', 'city', 'is_phone_verified', 'is_email_verified', 'created_at')
    list_filter = ('is_phone_verified', 'is_email_verified', 'city')
    search_fields = ('user__username', 'user__email', 'phone_number')


admin.site.register(PassengerProfile, PassengerProfileAdmin)
