from django.db import transaction
from rest_framework import serializers
from .models import OrderStop,Order
from directory.models import *
from clients.models import Counterparty

class OrderStopSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only = True)
    order_id = serializers.PrimaryKeyRelatedField(
        queryset = Order.objects.all(), 
        source = "order", 
        write_only = True, 
        required=False
    )

    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
        required=False,
    )

    location_title = serializers.SerializerMethodField(read_only=True)

    stop_type_display = serializers.CharField(
        source = "get_stop_type_display",
        read_only = True
    )

    class Meta:
        model = OrderStop
        fields = [
            "id",
            "company_id",
            "order_id",
            "location_id",
            "location_title",
            "sequence",
            "stop_type",         
            "stop_type_display",  
            "planned_date",
            "notes",
        ]
        read_only_fields = ["id",]

    def get_location_title(self,obj):
        if obj.location:
            return f"{obj.location.city}, {obj.location.address}"
        return None

    def validate_sequence(self,value):
        if value <= 0:
            raise serializers.ValidationError("Порядковий номер точки повинен бути більшим за 0.")
        return value


class OrderSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only = True)

    responsible_id = serializers.IntegerField(required=False)
    manager_name = serializers.CharField(required=False, allow_blank = True)

    status_display = serializers.CharField(
        source = "get_status_display",
        read_only = True
    )
    client_id = serializers.PrimaryKeyRelatedField(
        queryset = Counterparty.objects.filter(is_client = True),
        source = "client",
        write_only = True,
        required = False,
        allow_null = True,
    )
    client_name = serializers.CharField(
        source = "client.name",
        read_only = True
    )
    carrier_id = serializers.PrimaryKeyRelatedField(
        queryset = Counterparty.objects.filter(is_carrier = True),
        source = "carrier",
        write_only = True,
        required = False,
        allow_null = True,
    )
    carrier_name = serializers.CharField(
        source = "carrier.name",
        read_only = True
    )
    cargo_id = serializers.PrimaryKeyRelatedField(
        queryset = Cargo.objects.all(),
        source = "cargo",
        write_only = True,
        required = False,
        allow_null = True,
    )
    cargo_title = serializers.CharField(
        source = "cargo.title",
        read_only = True,
    )
    vehicle_id = serializers.PrimaryKeyRelatedField(
        queryset = Vehicle.objects.all(),
        source = "vehicle",
        write_only = True,
        required = False,
        allow_null = True,
    )
    vehicle_plate = serializers.CharField(
        source = "vehicle.plate_number",
        read_only = True,
    )
    trailer_id = serializers.PrimaryKeyRelatedField(
        queryset = Trailer.objects.all(),
        source = "trailer",
        write_only = True,
        required = False,
        allow_null = True,
    )
    trailer_body_type_display = serializers.CharField(
        source = "trailer.get_body_type_display",
        read_only = True,
    )
    trailer_plate = serializers.CharField(
        source = "trailer.plate_number",
        read_only = True
    )

    driver_id = serializers.PrimaryKeyRelatedField(
        queryset = Contact.objects.filter(is_driver=True),
        source = "driver",
        write_only = True,
        required = False,
        allow_null = True
    )
    driver_full_name = serializers.SerializerMethodField(read_only = True)
    driver_number = serializers.CharField(
        source = "driver.phone",
        read_only = True
    )

    client_currency_display = serializers.CharField(
        source = "get_client_currency_display",
        read_only = True
    )

    carrier_currency_display = serializers.CharField(
        source = "get_carrier_currency_display",
        read_only = True
    )

    payments_term_display = serializers.CharField(
        source = "get_payments_term_display",
        read_only = True
    )

    border_display = serializers.CharField(
        source = "get_border_display",
        read_only = True
    )
    stops = OrderStopSerializer(many=True, source="stops",required = False)
    class Meta:
        model = Order
        fields = [
            "id",
            "company_id",
            "status",
            "status_display",
            "responsible_id",
            "manager_name",
            "client_id",
            "client_name",
            "carrier_id",
            "carrier_name",
            "cargo_id",
            "cargo_title",
            "stops",
            "vehicle_id",
            "vehicle_plate",
            "trailer_id",
            "trailer_body_type_display",
            "trailer_plate",
            "driver_id",
            "driver_full_name",
            "driver_number",
            "client_currency",
            "client_currency_display",
            "client_price",
            "carrier_currency",
            "carrier_currency_display",
            "carrier_price",
            "payments_term",
            "payments_term_display",
            "border",
            "border_display",
            "notes",
            "created_at",
            "updated_at",
        ]

        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def get_driver_full_name(self, obj):
        if obj.driver:
            return f"{obj.driver.first_name} {obj.driver.last_name} {obj.driver.fathers_name}"
        return None
    
    @transaction.atomic
    def create(self, validated_data):
        stops_data = validated_data.pop("stops", [])
        order = Order.objects.create(**validated_data)
        for stop_item in stops_data:
            OrderStop.objects.create(order = order, **stop_item)

        return order

    @transaction.atomic
    def update(self, instance, validated_data):
        stops_data = validated_data.pop("stops", None)

        instance = super().update(instance, validated_data)

        if stops_data is not None:
            instance.stops.all().delete()
            for stop_item in stops_data:
                OrderStop.objects.create(order=instance, **stop_item)

        return instance