from rest_framework import serializers
from .models import Invoice, InvoiceItem


class InvoiceItemSerializer(serializers.ModelSerializer):
    line_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = InvoiceItem
        fields = ["id", "description", "qty", "unit_price", "line_total", "sort_order"]


class InvoiceSerializer(serializers.ModelSerializer):
    items = InvoiceItemSerializer(many=True, read_only=True)
    lead_id = serializers.SerializerMethodField()
    lead = serializers.SerializerMethodField()

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number", "type", "status", "client_name", "client_email",
            "lead", "lead_id", "issued_date", "due_date", "paid_date",
            "subtotal", "vat", "total", "notes", "items", "created_at", "updated_at",
        ]

    def get_lead_id(self, obj):
        return str(obj.lead_id) if obj.lead_id else None

    def get_lead(self, obj):
        if not obj.lead_id:
            return None
        lead = obj.lead
        return {"id": lead.id, "name": lead.name, "email": lead.email}


class InvoiceCreateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
    )
    lead_id = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Invoice
        fields = [
            "type", "client_name", "client_email", "lead_id", "issued_date", "due_date",
            "notes", "items",
        ]

    def validate_lead_id(self, value):
        if not value:
            return value
        from leads.models import Lead
        if not Lead.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Lead not found.")
        return value

    def create(self, validated_data):
        items_data = validated_data.pop("items")
        lead_id = validated_data.pop("lead_id", None)
        from leads.models import Lead
        from .number_generator import generate_invoice_number
        validated_data["invoice_number"] = generate_invoice_number(validated_data.get("type", "invoice"))
        if lead_id:
            validated_data["lead"] = Lead.objects.get(pk=lead_id)
        issued = validated_data.pop("issued_date", None)
        inv = Invoice.objects.create(**validated_data)
        if issued:
            inv.issued_date = issued
            inv.save(update_fields=["issued_date"])
        for i, item in enumerate(items_data):
            InvoiceItem.objects.create(
                invoice=inv,
                description=item.get("description", ""),
                qty=item.get("qty", 1),
                unit_price=item.get("unit_price", 0),
                sort_order=i,
            )
        inv.recalculate_totals()
        return inv


class InvoiceUpdateSerializer(serializers.ModelSerializer):
    items = serializers.ListField(child=serializers.DictField(), write_only=True)
    lead_id = serializers.CharField(required=False, allow_null=True)

    class Meta:
        model = Invoice
        fields = [
            "client_name", "client_email", "lead_id", "issued_date", "due_date",
            "notes", "items",
        ]

    def validate_lead_id(self, value):
        if not value:
            return value
        from leads.models import Lead
        if not Lead.objects.filter(pk=value).exists():
            raise serializers.ValidationError("Lead not found.")
        return value

    def update(self, instance, validated_data):
        items_data = validated_data.pop("items")
        lead_id = validated_data.pop("lead_id", None)
        from leads.models import Lead
        if lead_id is not None:
            instance.lead = Lead.objects.get(pk=lead_id) if lead_id else None
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()
        instance.items.all().delete()
        for i, item in enumerate(items_data):
            InvoiceItem.objects.create(
                invoice=instance,
                description=item.get("description", ""),
                qty=item.get("qty", 1),
                unit_price=item.get("unit_price", 0),
                sort_order=i,
            )
        instance.recalculate_totals()
        return instance
