from rest_framework import viewsets, permissions, filters
from django_filters.rest_framework import DjangoFilterBackend

from .models import Order
from .serializers import OrderSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ["status", "manager_name", "client", "carrier", "cargo", "payment_term", "border"]
    search_fields = ["client__name",
                    "carrier__name",       
                    "cargo__title",        
                    "vehicle__plate_number",
                    "trailer__plate_number",
                    "driver__last_name"
                    ]
    ordering_fields = ["status", "created_at", "client_price", "carrier_price"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Order.objects
            .filter(company_id=self.request.user.company_id)
            .select_related("client", "carrier", "cargo", "driver", "vehicle", "trailer")
            .prefetch_related("stops")
        )

    def perform_create(self, serializer):
            user = self.request.user
            responsible_id = serializer.validated_data.get("responsible_id", user.id)
            manager_name = serializer.validated_data.get("manager_name", getattr(user, "full_name", user.username))
            serializer.save(company_id=user.company_id, responsible_id=responsible_id, manager_name=manager_name)