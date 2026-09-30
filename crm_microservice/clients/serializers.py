from rest_framework import serializers
from .models import Counterparty
from directory.models import Location, BankingDetail, Contact


class CounterpartySerializer(serializers.ModelSerializer):
    company_id = serializers.IntegerField(read_only=True)

    location_id = serializers.PrimaryKeyRelatedField(
        queryset=Location.objects.all(),
        source="location",
        write_only=True,
        required=False,
        allow_null=True,
    )
    payment_detail_id = serializers.PrimaryKeyRelatedField(
        queryset=BankingDetail.objects.all(),
        source="payment_details",
        write_only=True,
        required=False,
        allow_null=True,
    )
    primary_contact_id = serializers.PrimaryKeyRelatedField(
        queryset=Contact.objects.all(),
        source="primary_contact", 
        write_only=True,
        required=False,
        allow_null=True,
    )

    location_address = serializers.CharField(
        source="location.address",
        read_only=True,
        default=None,
    )
    payment_details_iban = serializers.CharField(
        source="payment_details.iban",
        read_only=True,
        default=None,
    )
    primary_contact_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Counterparty
        fields = [
            "id",
            "company_id",
            "name",
            "is_client",
            "is_carrier",
            "location_id",
            "location_address",
            "payment_detail_id",
            "payment_details_iban",
            "primary_contact_id",
            "primary_contact_name",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_primary_contact_name(self, obj):
        if obj.primary_contact:
            return str(obj.primary_contact)
        return None

    def validate_name(self, value):
        return value.strip()

    def validate(self, attrs):
        is_client = attrs.get("is_client", getattr(self.instance, "is_client", False))
        is_carrier = attrs.get("is_carrier", getattr(self.instance, "is_carrier", False))

        if not is_client and not is_carrier:
            raise serializers.ValidationError(
                "Контрагент повинен бути або клієнтом, або перевізником (або обома)."
            )
        return attrs