from django.db import transaction
from .models import Lead


def generate_lead_id():
    with transaction.atomic():
        last = Lead.objects.select_for_update().order_by("-created_at").first()
        if last:
            num = int(last.id[1:]) + 1
        else:
            num = 1
        return f"L{num:03d}"
