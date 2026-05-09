from django.contrib import admin
from .models import Booking, Contract, Payment, Rating, Invoice, Refund


class PaymentInline(admin.TabularInline):
    model = Payment
    extra = 0
    readonly_fields = ('payment_reference', 'created_at', 'paid_at')


class ContractInline(admin.TabularInline):
    model = Contract
    extra = 0


class BookingAdmin(admin.ModelAdmin):
    list_display = ('id', 'passenger', 'driver', 'status', 'total_price', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('passenger__user__email', 'driver__user__email')
    inlines = [PaymentInline, ContractInline]

    actions = ['mark_completed']

    def mark_completed(self, request, queryset):
        queryset.update(status='completed')
    mark_completed.short_description = "Mark selected bookings as Completed"


class PaymentAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'amount', 'status', 'payment_type', 'payment_reference', 'paid_at')
    list_filter = ('status', 'payment_type')
    search_fields = ('booking__id', 'payment_reference')
    readonly_fields = ('payment_reference', 'created_at', 'paid_at')


class ContractAdmin(admin.ModelAdmin):
    list_display = ('contract_number', 'booking', 'status', 'contract_date')
    list_filter = ('status',)
    search_fields = ('contract_number',)


class RefundAdmin(admin.ModelAdmin):
    list_display = ('id', 'booking', 'refund_amount', 'status', 'created_at')
    list_filter = ('status',)

    actions = ['process_refunds']

    def process_refunds(self, request, queryset):
        queryset.update(status='processed')
    process_refunds.short_description = "Mark selected refunds as Processed"


admin.site.register(Booking, BookingAdmin)
admin.site.register(Payment, PaymentAdmin)
admin.site.register(Contract, ContractAdmin)
admin.site.register(Rating)
admin.site.register(Invoice)
admin.site.register(Refund, RefundAdmin)
