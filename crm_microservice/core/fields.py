from rest_framework import serializers

class CompanyScopedPKField(serializers.PrimaryKeyRelatedField):
    def get_queryset(self):
        queryset = super().get_queryset()
        request = self.context.get("request")
        if not request:
            return queryset.none()
        return queryset.filter(company_id = request.user.company_id)