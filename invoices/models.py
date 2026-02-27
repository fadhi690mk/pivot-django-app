import uuid
from decimal import Decimal
from django.db import models


class Invoice(models.Model):
    TYPE_CHOICES = [("invoice", "Invoice"), ("receipt", "Receipt")]
    STATUS_CHOICES = [
        ("draft", "Draft"),
        ("sent", "Sent"),
        ("paid", "Paid"),
        ("overdue", "Overdue"),
        ("cancelled", "Cancelled"),
    ]
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice_number = models.CharField(max_length=30, unique=True)
    type = models.CharField(max_length=10, choices=TYPE_CHOICES, default="invoice")
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="draft")
    client_name = models.CharField(max_length=255)
    client_email = models.EmailField()
    lead = models.ForeignKey(
        "leads.Lead", null=True, blank=True, on_delete=models.SET_NULL, related_name="invoices"
    )
    issued_date = models.DateField(auto_now_add=True)
    due_date = models.DateField(blank=True, null=True)
    paid_date = models.DateField(blank=True, null=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    vat = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    notes = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "invoices_invoice"

    def recalculate_totals(self):
        from decimal import Decimal
        st = sum(i.line_total for i in self.items.all())
        self.subtotal = st
        self.vat = round(st * Decimal("0.05"))
        self.total = self.subtotal + self.vat
        self.save(update_fields=["subtotal", "vat", "total", "updated_at"])


class InvoiceItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name="items")
    description = models.CharField(max_length=500)
    qty = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "invoices_invoice_item"

    @property
    def line_total(self):
        return self.qty * self.unit_price
