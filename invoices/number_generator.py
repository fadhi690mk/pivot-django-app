from django.db import transaction
from datetime import date
from .models import Invoice


def generate_invoice_number(invoice_type="invoice"):
    prefix = "INV" if invoice_type == "invoice" else "REC"
    year = date.today().year
    with transaction.atomic():
        last = (
            Invoice.objects.filter(invoice_number__startswith=f"{prefix}-{year}-")
            .order_by("-invoice_number")
            .first()
        )
        if last:
            num = int(last.invoice_number.split("-")[-1]) + 1
        else:
            num = 1
        return f"{prefix}-{year}-{num:03d}"
