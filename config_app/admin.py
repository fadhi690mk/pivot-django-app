from django.contrib import admin
from .models import BusinessActivity, Jurisdiction, CalculatorService, SearchSuggestion

admin.site.register(BusinessActivity)
admin.site.register(Jurisdiction)
admin.site.register(CalculatorService)
admin.site.register(SearchSuggestion)
