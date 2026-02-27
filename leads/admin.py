from django.contrib import admin
from .models import Lead, LeadNote, LeadTag

try:
    from ai_sales.models import ChatMessage

    class ChatMessageInline(admin.TabularInline):
        model = ChatMessage
        fk_name = "lead"
        extra = 0
        readonly_fields = ["session", "role", "content", "token_count", "created_at"]
        can_delete = False

        def has_add_permission(self, request, obj=None):
            return False

    _INLINES = [ChatMessageInline]
except ImportError:
    _INLINES = []


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "email", "source", "status", "priority", "created_at"]
    readonly_fields = ["chat_summary", "ai_session_id", "chat_message_count"]
    inlines = _INLINES

    def chat_message_count(self, obj):
        if not obj.pk:
            return 0
        try:
            return obj.chat_messages.count()
        except Exception:
            return 0

    chat_message_count.short_description = "Chat message count"


admin.site.register(LeadNote)
admin.site.register(LeadTag)
