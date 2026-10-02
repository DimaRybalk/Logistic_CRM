from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Counterparty
from .serializers import CounterpartySerializer

class CounterpartyViewSet(viewsets.ModelViewSet):
    serializer_class = CounterpartySerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["is_client", "is_carrier"]
    search_fields = ["name"]
    orderig_fields = ["name","created_at"]

    def get_queryset(self):
        user = self.request.user
        return Counterparty.objects.filter(company_id = user.company_id).select_related("location","payment_details","primary_contact")

    def perform_create(self, serializer):
        serializer.save(company_id=self.request.user.company_id)