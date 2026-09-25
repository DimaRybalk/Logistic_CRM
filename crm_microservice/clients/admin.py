from django.contrib import admin

from clients.models import Counterparty

@admin.register(Counterparty)
class CounterpartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_client', 'is_carrier', 'primary_contact', 'location', 'company_id')
    list_filter = ('is_client', 'is_carrier', 'company_id')
    search_fields = ('name', 'primary_contact__last_name', 'primary_contact__phone')
    autocomplete_fields = ('location', 'payment_details', 'primary_contact')
