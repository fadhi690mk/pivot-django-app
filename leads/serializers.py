from rest_framework import serializers
from .models import Lead, LeadNote, LeadTag


class LeadNoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadNote
        fields = ["id", "text", "author", "created_at"]
        read_only_fields = ["author", "created_at"]


class LeadTagSerializer(serializers.ModelSerializer):
    class Meta:
        model = LeadTag
        fields = ["id", "name"]


class LeadListSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    notes_count = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id", "name", "email", "phone", "company", "source", "status", "priority",
            "service", "service_interest", "sub_service", "jurisdiction", "estimated_value",
            "assigned_to", "tags", "created_at", "last_contacted_at", "notes_count",
        ]

    def get_assigned_to(self, obj):
        if obj.assigned_to:
            return {"id": str(obj.assigned_to.id), "name": obj.assigned_to.name}
        return None

    def get_service(self, obj):
        if obj.service_id and obj.service:
            return {"id": str(obj.service.id), "slug": obj.service.slug, "title": obj.service.title}
        return None

    def get_tags(self, obj):
        return list(obj.tags.values_list("name", flat=True))

    def get_notes_count(self, obj):
        return obj.notes.count()


class LeadDetailSerializer(serializers.ModelSerializer):
    assigned_to = serializers.SerializerMethodField()
    service = serializers.SerializerMethodField()
    tags = LeadTagSerializer(many=True, read_only=True)
    notes = LeadNoteSerializer(many=True, read_only=True)
    chat_summary = serializers.CharField(read_only=True, allow_null=True)
    ai_session_id = serializers.CharField(read_only=True, allow_null=True)
    chat_messages = serializers.SerializerMethodField()

    class Meta:
        model = Lead
        fields = [
            "id", "name", "email", "phone", "company", "source", "status", "priority",
            "service", "service_interest", "sub_service", "jurisdiction", "estimated_value",
            "assigned_to", "tags", "notes", "created_at", "last_contacted_at", "updated_at",
            "chat_summary", "ai_session_id", "chat_messages",
        ]

    def get_assigned_to(self, obj):
        if obj.assigned_to:
            return {"id": str(obj.assigned_to.id), "name": obj.assigned_to.name}
        return None

    def get_service(self, obj):
        if obj.service_id and obj.service:
            return {"id": str(obj.service.id), "slug": obj.service.slug, "title": obj.service.title}
        return None

    def get_chat_messages(self, obj):
        if not obj.pk:
            return []
        try:
            return list(obj.chat_messages.order_by("created_at").values("role", "content", "created_at"))
        except Exception:
            return []


class LeadCreatePublicSerializer(serializers.ModelSerializer):
    tags = serializers.ListField(child=serializers.CharField(), required=False, default=list)
    service_id = serializers.CharField(required=False, allow_null=True)
    priority = serializers.CharField(required=False, default="medium")
    message = serializers.CharField(required=False, allow_blank=True, write_only=True)
    ai_session_id = serializers.CharField(required=False, allow_null=True, allow_blank=True)

    class Meta:
        model = Lead
        fields = [
            "name", "email", "phone", "company", "source", "service_id", "service_interest",
            "sub_service", "jurisdiction", "estimated_value", "priority", "tags", "message",
            "ai_session_id",
        ]

    def create(self, validated_data):
        tags = validated_data.pop("tags", [])
        service_id = validated_data.pop("service_id", None)
        message = validated_data.pop("message", "").strip()
        ai_session_id = (validated_data.pop("ai_session_id", None) or "").strip()
        from .id_generator import generate_lead_id
        validated_data["id"] = generate_lead_id()
        if service_id:
            from cms.models import Service
            try:
                validated_data["service"] = Service.objects.get(pk=service_id)
            except Service.DoesNotExist:
                pass
        if ai_session_id:
            validated_data["source"] = validated_data.get("source") or "ai_chatbot"
            validated_data["ai_session_id"] = ai_session_id[:255]
        lead = Lead.objects.create(**validated_data)
        for t in tags:
            LeadTag.objects.create(lead=lead, name=t)
        if message:
            LeadNote.objects.create(lead=lead, text=message, author="Contact form")
        if ai_session_id:
            try:
                from ai_sales.models import ChatSession
                from ai_sales.services.summary_service import update_lead_summary
                session = ChatSession.objects.filter(session_id=ai_session_id).first()
                if session:
                    session.lead = lead
                    session.save(update_fields=["lead"])
                    session.messages.update(lead=lead)
                    update_lead_summary(lead)
            except Exception as e:
                import logging
                logging.getLogger(__name__).warning("Link chat session to lead failed: %s", e)
        return lead
