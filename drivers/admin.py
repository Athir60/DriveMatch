from django.contrib import admin
from django.utils.html import format_html

from .models import (
    DriverProfile, Vehicle, Route, DriverRoute,
    SubscriptionPlan, DriverSubscription, FavoriteDriver,
    DriverCancellationRequest, DriverBankAccount,
    DriverSubscriptionPayment
)


class DriverProfileAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'phone_number',
        'verification_status',
        'profile_photo_preview',
    )

    fields = (
        'user',
        'phone_number',
        'national_id',

        'profile_photo_preview',
        'profile_photo',

        'id_front_preview',
        'id_front',

        'id_back_preview',
        'id_back',

        'driver_license_preview',
        'driver_license',

        'verification_status',
        'average_rating',
        'total_trips',
        'bio',
    )

    readonly_fields = (
        'profile_photo_preview',
        'id_front_preview',
        'id_back_preview',
        'driver_license_preview',
    )


    def profile_photo_preview(self, obj):
        if obj.profile_photo:
            return format_html(
                '<img src="{}" width="80" style="border-radius:50%;" />',
                obj.profile_photo.url
            )
        return "No Image"

    profile_photo_preview.short_description = "Profile Photo Preview"

    def id_front_preview(self, obj):
        if obj.id_front:
            return format_html('<img src="{}" width="120" />', obj.id_front.url)
        return "No Image"

    id_front_preview.short_description = "ID Front Preview"

    def id_back_preview(self, obj):
        if obj.id_back:
            return format_html('<img src="{}" width="120" />', obj.id_back.url)
        return "No Image"

    id_back_preview.short_description = "ID Back Preview"

    def driver_license_preview(self, obj):
        if obj.driver_license:
            return format_html('<img src="{}" width="120" />', obj.driver_license.url)
        return "No Image"

    driver_license_preview.short_description = "License Preview"


    def approve_drivers(self, request, queryset):
        queryset.update(verification_status='approved')
        self.message_user(request, "Selected drivers have been approved.")

    approve_drivers.short_description = "Approve selected drivers"

    def reject_drivers(self, request, queryset):
        queryset.update(verification_status='rejected')
        self.message_user(request, "Selected drivers have been rejected.")

    reject_drivers.short_description = "Reject selected drivers"


class VehicleAdmin(admin.ModelAdmin):
    list_display = ('driver', 'brand', 'model', 'year', 'color', 'license_plate', 'car_type')
    list_filter = ('car_type', 'brand')
    search_fields = ('license_plate', 'brand', 'model')


class RouteAdmin(admin.ModelAdmin):
    list_display = ('from_area', 'to_area', 'city')
    list_filter = ('city',)
    search_fields = ('from_area', 'to_area')


class DriverRouteAdmin(admin.ModelAdmin):
    list_display = ('driver', 'route', 'monthly_price', 'commitment_duration', 'is_active')
    list_filter = ('commitment_duration', 'is_active')


class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'duration_days', 'is_active')
    list_filter = ('is_active',)


class DriverSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('driver', 'plan', 'start_date', 'end_date', 'is_active')
    list_filter = ('is_active', 'plan')


class DriverCancellationRequestAdmin(admin.ModelAdmin):
    list_display = ('driver', 'booking', 'status', 'submitted_at')
    list_filter = ('status',)
    search_fields = ('driver__user__username',)


class DriverBankAccountAdmin(admin.ModelAdmin):
    list_display = ('driver', 'bank_name', 'iban', 'account_holder_name', 'is_active', 'created_at')
    list_filter = ('is_active', 'bank_name')
    search_fields = ('driver__user__username', 'iban', 'account_holder_name')


class DriverSubscriptionPaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'driver', 'plan', 'amount', 'status', 'payment_reference', 'created_at', 'paid_at')
    list_filter = ('status', 'plan')
    search_fields = ('driver__user__email', 'payment_reference')
    readonly_fields = ('payment_reference', 'created_at', 'paid_at')



admin.site.register(DriverProfile, DriverProfileAdmin)
admin.site.register(Vehicle, VehicleAdmin)
admin.site.register(Route, RouteAdmin)
admin.site.register(DriverRoute, DriverRouteAdmin)
admin.site.register(SubscriptionPlan, SubscriptionPlanAdmin)
admin.site.register(DriverSubscription, DriverSubscriptionAdmin)
admin.site.register(FavoriteDriver)
admin.site.register(DriverCancellationRequest, DriverCancellationRequestAdmin)
admin.site.register(DriverBankAccount, DriverBankAccountAdmin)
admin.site.register(DriverSubscriptionPayment, DriverSubscriptionPaymentAdmin)