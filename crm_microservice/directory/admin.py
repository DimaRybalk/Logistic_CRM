from django.contrib import admin
from .models import (
    Location,
    BankingDetail,
    Contact,
    Cargo,
    CargoItem,
    Vehicle,
    Trailer,
)

@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ('city', 'address', 'country', 'region', 'postal_code', 'company_id')
    list_filter = ('country', 'company_id')
    search_fields = ('city', 'address', 'region')

@admin.register(BankingDetail)
class BankingDetailAdmin(admin.ModelAdmin):
    list_display = ('title', 'legal_form', 'tax_number', 'iban', 'is_default', 'company_id')
    list_filter = ('legal_form', 'is_default', 'company_id')
    search_fields = ('title', 'tax_number', 'iban')

@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'phone', 'email', 'counterparty', 'is_driver', 'is_client', 'is_carrier')
    list_filter = ('is_driver', 'is_client', 'is_carrier', 'adr_status', 'company_id')
    search_fields = ('last_name', 'first_name', 'phone', 'email', 'driver_license')


class CargoItemInline(admin.TabularInline):
    model = CargoItem
    extra = 1
    fields = ('name', 'packaging_type', 'quantity', 'weight_gross_kg', 'volume_m3', 'length', 'width', 'height')

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_hazardous', 'adr_class', 'requires_temperature_control', 'company_id')
    list_filter = ('is_hazardous', 'requires_temperature_control', 'company_id')
    search_fields = ('title',)
    inlines = [CargoItemInline]


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'name', 'carrier', 'carrying_capacity_kg', 'has_adr', 'is_active')
    list_filter = ('has_adr', 'is_active', 'company_id')
    search_fields = ('plate_number', 'vin_code', 'name')


@admin.register(Trailer)
class TrailerAdmin(admin.ModelAdmin):
    list_display = ('plate_number', 'body_type', 'carrier', 'volume_m3', 'capacity_pallets', 'is_active')
    list_filter = ('body_type', 'is_active', 'company_id')
    search_fields = ('plate_number',)