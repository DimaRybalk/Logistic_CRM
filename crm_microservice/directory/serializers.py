from decimal import Decimal

from rest_framework import serializers
from .models import *
from clients.models import Counterparty
import re
from django.db import transaction

class LocationSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    country_display = serializers.CharField(source="get_country_display",read_only=True)

    class Meta:
        model = Location
        fields = [
            "company_id",
            "id",
            "country",
            "country_display",
            "postal_code",
            "region",
            "city",
            "address",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_address(self, value):
        return value.strip()

class BankingDetailSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    legal_form_display = serializers.CharField(source="get_legal_form_display", read_only=True)

    class Meta:
        model = BankingDetail
        fields = [
            "company_id",
            "id",
            "legal_form",
            "legal_form_display",
            "title",
            "tax_number",
            "iban",
            "is_default",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate_tax_number(self,value):
        return value.strip()
    
    def validate_iban(self,value):
        cleaned_iban = re.sub(r"\s+","",value).upper()
        if len(cleaned_iban) < 15:
            raise serializers.ValidationError("Номер IBAN / рахунку занадто короткий")
        return cleaned_iban
    
    @transaction.atomic
    def create(self,validated_data):
        is_default = validated_data.get("is_default", False)
        company_id = validated_data.get("company_id")
        if is_default and company_id:
            BankingDetail.objects.filter(
                company_id=company_id,
                is_default=True
            ).update(is_default=False)
        return super().create(validated_data)
    
    @transaction.atomic
    def update(self, instance, validated_data):
        is_default = validated_data.get("is_default", instance.is_default)
        company_id = instance.company_id
        if is_default and not instance.is_default:
            BankingDetail.objects.filter(
                company_id=company_id,
                is_default=True
            ).exclude(id=instance.id).update(is_default=False)
        return super().update(instance, validated_data)

class ContactSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    
    counterparty_id = serializers.PrimaryKeyRelatedField(
        queryset = Counterparty.objects.all(), source="counterparty", write_only=True, required=False, allow_null = False
    )

    counterparty_name = serializers.CharField(
        source = "counterparty.name",
        read_only = True,
        default = None
    )

    adr_status_display = serializers.CharField(
        source="get_adr_status_display",
        read_only = True
    )

    class Meta:
        model = Contact
        fields = [
            "id",
            "company_id",
            "first_name",
            "last_name",
            "fathers_name",
            "phone",
            "secondary_phone",
            "email",
            "counterparty_id",
            "counterparty_name",
            "is_driver",
            "is_client",
            "is_carrier",
            "is_custom_officer",
            "is_warehouse_worker",
            "adr_status",
            "adr_status_display",
            "driver_license",
            "passport_number",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id","created_at","updated_at"]

    def validate_driver_license(self, value):
        return value.strip() if value else value
    
    def validate_passport_number(self, value):
        return value.strip() if value else value

class CargoItemSerializer(serializers.ModelSerializer):
    
    cargo_title = serializers.CharField(
        source = "cargo.title", read_only = True
    )
    packaging_type_display = serializers.CharField(
        source = "get_packaging_type_display",
        read_only=True
    )
    class Meta:
        model = CargoItem
        fields = [
            "id",
            "cargo_title",
            "name",
            "packaging_type",
            "packaging_type_display",
            "quantity",
            "weight_gross_kg",
            "volume_m3",
            "length",
            "width",
            "height"
        ]
        read_only_fields = ["id"]

    def validate_name(self, value):
        return value.strip()
    
    def validate(self, attrs):
        length = attrs.get("length", getattr(self.instance, "length", None))
        width = attrs.get("width", getattr(self.instance, "width", None))
        height = attrs.get("height", getattr(self.instance, "height", None))
        volume = attrs.get("volume_m3", getattr(self.instance, "volume_m3", None))

        if not volume and length and width and height:
            calculated_volume = (length * width * height) / Decimal("1000000.0")
            attrs["volume_m3"] = round(calculated_volume, 2)

        return attrs


class CargoSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    adr_class_display = serializers.CharField(
        source = "get_adr_class_display",
        read_only = True
    )
    cargo_items = CargoItemSerializer(many=True, source="items", required=False)

    class Meta:
        model = Cargo
        fields = [
            "id",
            "company_id",
            "title",
            "cargo_items",
            "is_hazardous",
            "adr_class",
            "adr_class_display",
            "requires_temperature_control",
            "temperature_min",
            "temperature_max",
            "notes",
            "created_at",
            "updated_at",

        ]
        read_only_fields = ["id","created_at","updated_at"]

    def validate(self, attrs):
        temp_required = attrs.get(
            "requires_temperature_control",
            getattr(self.instance, "requires_temperature_control", False)
        )
        t_min = attrs.get("temperature_min", getattr(self.instance, "temperature_min", None))
        t_max = attrs.get("temperature_max", getattr(self.instance, "temperature_max", None))

        if temp_required and (t_min is None or t_max is None):
            raise serializers.ValidationError("Для вантажу з температурним режимом обов'язково вказати мінімальну та максимальну температуру.")

        if t_min is not None and t_max is not None and t_min >= t_max:
            raise serializers.ValidationError(
                "Мінімальна температура не може бути вищою за максимальну або дорівнюти їй"
            )

        return attrs

    @transaction.atomic
    def create(self,validated_data):
        items_data = validated_data.pop("items",[ ])
        cargo = Cargo.objects.create(**validated_data)
        for item in items_data:
            CargoItem.objects.create(cargo=cargo, **item)

        return cargo

    @transaction.atomic
    def update(self,instance,validated_data):
        items_data = validated_data.pop("items",None)
        instance = super().update(instance, validated_data)
        if items_data is not None:
            instance.items.all().delete()
            for item in items_data:
                CargoItem.objects.create(cargo=instance, **item)
        return instance

class VehicleSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    carrier_id = serializers.PrimaryKeyRelatedField(
            queryset = Counterparty.objects.all(), source="carrier", write_only=True, required=False, allow_null = False
        )
    
    carrier_name = serializers.CharField(
            source = "carrier.name",
            read_only = True,
            default = None
        )

    class Meta:
        model = Vehicle
        fields = [
            "id",
            "company_id",
            "carrier_id",
            "carrier_name",
            "name",
            "plate_number",
            "vin_code",
            "registration_certificate",
            "carrying_capacity_kg",
            "has_adr",
            "is_active",
            "notes",
            "created_at",
            "updated_at"

        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at"
        ]   

    def validate_plate_number(self, value):
        cleaned = re.sub(r"[\s\-]+", "", value).upper()
        if len(cleaned) < 4:
            raise serializers.ValidationError("Номерний знак занадто короткий.")
        return cleaned

    def validate_vin_code(self, value):
        if not value:
            return value
        cleaned = re.sub(r"[\s\-]+", "", value).upper()
        if len(cleaned) != 17:
            raise serializers.ValidationError("VIN-код повинен містити рівно 17 символів.")
        return cleaned

    def validate_carrier_id(self, counterparty: Counterparty):
        if not counterparty.is_carrier:
            raise serializers.ValidationError("Обраний контрагент не є перевізником.")
        return counterparty

class TrailerSerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)
    
    
    carrier_id = serializers.PrimaryKeyRelatedField(
        queryset=Counterparty.objects.all(),
        source="carrier",
        write_only=True,
    )
    
    carrier_name = serializers.CharField(
        source="carrier.name",
        read_only=True,
        default=None,
    )

    body_type_display = serializers.CharField(
        source="get_body_type_display",
        read_only=True,
    )

    class Meta:
        model = Trailer
        fields = [
            "id",
            "company_id",
            "carrier_id",
            "carrier_name",
            "plate_number",
            "body_type",
            "body_type_display",
            "volume_m3",
            "capacity_pallets",
            "carrying_capacity_kg",
            "registration_certificate",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "updated_at",
        ]

    def validate_plate_number(self, value):
        cleaned = re.sub(r"[\s\-]+", "", value).upper()
        if len(cleaned) < 4:
            raise serializers.ValidationError("Номерний знак занадто короткий.")
        return cleaned

    def validate_carrier_id(self, counterparty):
        if not counterparty.is_carrier:
            raise serializers.ValidationError("Обраний контрагент не є перевізником.")
        return counterparty

    def validate(self, attrs):
        capacity_kg = attrs.get("carrying_capacity_kg", getattr(self.instance, "carrying_capacity_kg", None))
        pallets = attrs.get("capacity_pallets", getattr(self.instance, "capacity_pallets", None))

        if capacity_kg is not None and capacity_kg <= 0:
            raise serializers.ValidationError({"carrying_capacity_kg": "Вантажопідйомність повинна бути більшою за 0."})

        if pallets is not None and (pallets <= 0 or pallets > 66):
            raise serializers.ValidationError({"capacity_pallets": "Місткість палет зазвичай від 1 до 66 (для двоповерхових причепів)."})

        return attrs