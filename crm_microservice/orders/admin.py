from django.contrib import admin
from .models import Order, OrderStop

class OrderStopInline(admin.TabularInline):
    model = OrderStop
    extra = 2 
    fields = ('sequence', 'stop_type', 'location', 'planned_date', 'notes')
    ordering = ('sequence',)

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'status',
        'client',
        'carrier',
        'route_display_admin',
        'client_price_display',
        'carrier_price_display',
        'margin_display',
        'created_at',
    )
    list_filter = ('status', 'client_currency', 'carrier_currency', 'company_id', 'created_at')
    search_fields = ('id', 'client__name', 'carrier__name', 'manager_name')
    inlines = [OrderStopInline]

    fieldsets = (
        ("Службова інформація", {
            "fields": (("company_id", "responsible_id", "manager_name"), "status")
        }),
        ("Сторони перевезення", {
            "fields": (("client", "carrier"), ("vehicle", "trailer", "driver"), "cargo")
        }),
        ("Фінанси з клієнтом", {
            "fields": (("client_price", "client_currency"), "payments_term")
        }),
        ("Фінанси з перевізником", {
            "fields": (("carrier_price", "carrier_currency"), "border")
        }),
        ("Додатково", {
            "fields": ("notes",)
        }),
    )

    @admin.display(description="Маршрут")
    def route_display_admin(self, obj):
        return obj.route_title

    @admin.display(description="Ціна клієнта")
    def client_price_display(self, obj):
        return f"{obj.client_price} {obj.client_currency}" if obj.client_price else "-"

    @admin.display(description="Ставка перевізнику")
    def carrier_price_display(self, obj):
        return f"{obj.carrier_price} {obj.carrier_currency}" if obj.carrier_price else "-"

    @admin.display(description="Маржа")
    def margin_display(self, obj):
        m = obj.margin
        return f"{m} {obj.client_currency}" if m is not None else "-"