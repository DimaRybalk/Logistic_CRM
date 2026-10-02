from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LocationViewSet, BankingDetailViewSet, ContactViewSet, CargoViewSet, VehicleViewSet, TrailerViewSet

router = DefaultRouter()

router.register(r'locations', LocationViewSet, basename='location')
router.register(r'banking-details', BankingDetailViewSet, basename='banking-detail')
router.register(r'contacts', ContactViewSet, basename='contact')
router.register(r'cargos', CargoViewSet, basename='cargo')
router.register(r'vehicles', VehicleViewSet, basename='vehicle')
router.register(r'trailers', TrailerViewSet, basename='trailer')

urlpatterns = [
    path('', include(router.urls)),
]