from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class BaseModelViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        if getattr(self, "swager_fake_view", False):
            return self.queryset.none()

        user = self.request.user
        company_id = getattr(user, "company_id", None)

        if not company_id:
            return self.queryset.none()

        return self.queryset.filter(company_id=company_id)

    def perform_create(self, serializer):
        serializer.save(company_id = self.request.user.company_id)