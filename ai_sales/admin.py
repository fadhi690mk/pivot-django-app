from django.contrib import admin
from .models import ChatSession, ChatMessage


class ChatMessageInline(admin.TabularInline):
    model = ChatMessage
    fk_name = "session"
    extra = 0
    readonly_fields = ["role", "content", "token_count", "created_at"]


@admin.register(ChatSession)
class ChatSessionAdmin(admin.ModelAdmin):
    list_display = ["session_id", "lead", "created_at", "updated_at"]
    list_filter = ["created_at"]
    search_fields = ["session_id"]
    inlines = [ChatMessageInline]
    readonly_fields = ["session_id", "created_at", "updated_at"]


@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ["id", "session", "lead", "role", "content_preview", "created_at"]
    list_filter = ["role", "created_at"]

    def content_preview(self, obj):
        return (obj.content or "")[:80] + ("..." if len(obj.content or "") > 80 else "")

    content_preview.short_description = "Content"
