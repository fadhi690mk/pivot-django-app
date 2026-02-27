import uuid
from django.db import models


class BusinessActivity(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    label = models.CharField(max_length=100)
    icon = models.CharField(max_length=10, blank=True, null=True)
    status = models.CharField(max_length=15, default="published")
    sort_order = models.PositiveIntegerField(default=0)


class Jurisdiction(models.Model):
    id = models.CharField(primary_key=True, max_length=50)
    label = models.CharField(max_length=100)
    description = models.CharField(max_length=255, blank=True, null=True)
    base_price = models.PositiveIntegerField()
    status = models.CharField(max_length=15, default="published")


class CalculatorService(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    service = models.ForeignKey("cms.Service", on_delete=models.CASCADE)
    label = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    per = models.CharField(max_length=50)
    status = models.CharField(max_length=15, default="published")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "config_calculator_service"


class SearchSuggestion(models.Model):
    id = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True, null=True)
    type = models.CharField(max_length=20)
    href = models.CharField(max_length=255)
    status = models.CharField(max_length=15, default="published")
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        db_table = "config_search_suggestion"
