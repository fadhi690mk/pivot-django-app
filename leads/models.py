import uuid
from django.db import models
from core.models import BaseModel


class Lead(models.Model):
    SOURCE_CHOICES = [
        ("contact_form", "Contact Form"),
        ("quote_request", "Quote Request"),
        ("calculator", "Calculator"),
        ("whatsapp", "WhatsApp"),
        ("phone", "Phone"),
        ("popup", "Popup"),
        ("referral", "Referral"),
        ("ai_chatbot", "AI Chatbot"),
    ]
    STATUS_CHOICES = [
        ("new", "New"),
        ("contacted", "Contacted"),
        ("qualified", "Qualified"),
        ("proposal", "Proposal"),
        ("won", "Won"),
        ("lost", "Lost"),
    ]
    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ]
    id = models.CharField(primary_key=True, max_length=10, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    phone = models.CharField(max_length=30)
    company = models.CharField(max_length=255, blank=True, null=True)
    source = models.CharField(max_length=30, choices=SOURCE_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="new")
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default="medium")
    service_interest = models.CharField(max_length=255)
    sub_service = models.CharField(max_length=255, blank=True, null=True)
    jurisdiction = models.CharField(max_length=20, blank=True, null=True)
    estimated_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    service = models.ForeignKey(
        "cms.Service", null=True, blank=True, on_delete=models.SET_NULL, related_name="leads"
    )
    assigned_to = models.ForeignKey(
        "accounts.HubUser", null=True, blank=True, on_delete=models.SET_NULL, related_name="assigned_leads"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_contacted_at = models.DateTimeField(blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True)
    # AI chat: summary reused as memory; session_id links to ChatSession
    chat_summary = models.TextField(blank=True, null=True)
    ai_session_id = models.CharField(max_length=255, db_index=True, blank=True, null=True)

    class Meta:
        db_table = "leads_lead"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.id} - {self.name}"


class LeadNote(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="notes")
    text = models.TextField()
    author = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "leads_lead_note"


class LeadTag(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="tags")
    name = models.CharField(max_length=100)

    class Meta:
        db_table = "leads_lead_tag"
