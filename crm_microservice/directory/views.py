from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Location,BankingDetail,Contact,Cargo,Vehicle,Trailer
from .serializers import LocationSerializer,BankingDetailSerializer,ContactSerializer,CargoSerializer,VehicleSerializer,TrailerSerializer
from core.permissions import IsCompanyMember,IsForwarderPermission,IsOwnerPermission,IsViewerPermission


class LocationViewSet(viewsets.ModelViewSet):
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission | IsViewerPermission)]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["country", "city"]
    search_fields = ["country","city","address"]
    ordering_fields = ["created_at", "country", "city"]

    def get_queryset(self):
        user = self.request.user
        return Location.objects.filter(company_id=user.company_id)

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)

class BankingDetailViewSet(viewsets.ModelViewSet):
    serializer_class = BankingDetailSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission)]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["legal_form", "is_default"]
    search_fields = ["title", "iban", "tax_number", "bank_name"]
    ordering_fields = ["legal_form","title","created_at"]
    ordering = ["-is_default", "title"]

    def get_queryset(self):
        user = self.request.user
        return BankingDetail.objects.filter(company_id=user.company_id)

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)

class ContactViewSet(viewsets.ModelViewSet):
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission)]


    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "counterparty",
        "is_driver",
        "is_client",
        "is_carrier",
        "is_custom_officer",
        "is_warehouse_worker",
        "adr_status",
    ]

    search_fields = [
        "first_name",
        "last_name",
        "phone",
        "email",
        "counterparty__name",
    ]

    ordering_fields = ["last_name", "first_name", "created_at"]
    ordering = ["-created_at","last_name", "first_name"]

    def get_queryset(self):
        user = self.request.user
        return Contact.objects.filter(company_id=user.company_id).select_related("counterparty")

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)

class CargoViewSet(viewsets.ModelViewSet):
    serializer_class = CargoSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission | IsViewerPermission)]


    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "is_hazardous",
        "adr_class",
        "requires_temperature_control",
    ]
    search_fields = [
        "title",
        "items__description",
    ]

    ordering_fields = ["created_at", "title"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        return Cargo.objects.filter(
            company_id = user.company_id
        ).prefetch_related("items")

    def perform_create(self, serializer):
            serializer.save(company_id=self.request.user.company_id)

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission | IsViewerPermission)]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "carrier",
        "is_active",
        "has_adr",
        "carrying_capacity_kg",
    ]

    search_fields = [
        "plate_number",
        "name",
        "vin_code",
        "registration_certificate",
        "carrier__name",
    ]

    ordering_fields = ["created_at", "plate_number", "carrying_capacity_kg"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        return Vehicle.objects.filter(
            company_id = user.company_id
        ).select_related("carrier")

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)


class TrailerViewSet(viewsets.ModelViewSet):
    serializer_class = TrailerSerializer
    permission_classes = [permissions.IsAuthenticated & IsCompanyMember & (IsOwnerPermission | IsForwarderPermission | IsViewerPermission)]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = [
        "carrier",
        "is_active",
        "body_type",
        "volume_m3",
        "capacity_pallets",
        "carrying_capacity_kg"
    ]

    search_fields = [
        "plate_number",
        "registration_certificate",
        "carrier__name",
    ]

    ordering_fields = ["created_at", "plate_number", "carrying_capacity_kg"]
    ordering = ["-created_at"]

    def get_queryset(self):
        user = self.request.user
        return Trailer.objects.filter(
            company_id = user.company_id
        ).select_related("carrier")

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)

