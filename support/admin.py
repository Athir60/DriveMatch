from django.contrib import admin
from .models import Complaint, Ticket


class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('id', 'subject', 'submitted_by', 'booking', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('subject', 'submitted_by__username', 'submitted_by__email')
    readonly_fields = ('submitted_by', 'booking', 'created_at')
    fieldsets = (
        ('Complaint Information', {
            'fields': ('submitted_by', 'booking', 'subject', 'description')
        }),
        ('Admin Response', {
            'fields': ('status', 'admin_response')
        }),
        ('Dates', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )


class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number', 'subject', 'submitted_by', 'ticket_type',
        'category', 'related_id', 'status', 'created_at'
    )
    list_filter = ('status', 'ticket_type', 'category')
    search_fields = (
        'ticket_number', 'subject',
        'submitted_by__username', 'submitted_by__email',
        'related_id'
    )
    readonly_fields = ('ticket_number', 'submitted_by', 'created_at', 'updated_at')
    fieldsets = (
        ('Ticket Information', {
            'fields': (
                'ticket_number', 'submitted_by',
                'ticket_type', 'category',
                'subject', 'description',
                'related_id', 'attachment',
            )
        }),
        ('Admin Response', {
            'fields': ('status', 'admin_response'),
            'description': 'Change the status and write a response to the user here.',
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )


admin.site.register(Complaint, ComplaintAdmin)
admin.site.register(Ticket, TicketAdmin)
