from django.contrib import admin
from .models import MessageThread, Message


class MessageInline(admin.TabularInline):
    model = Message
    readonly_fields = ('sender', 'text', 'created_at', 'is_read')
    extra = 0


class MessageThreadAdmin(admin.ModelAdmin):
    list_display = ('passenger', 'driver', 'booking', 'created_at', 'updated_at')
    list_filter = ('created_at',)
    inlines = [MessageInline]


admin.site.register(MessageThread, MessageThreadAdmin)
admin.site.register(Message)
