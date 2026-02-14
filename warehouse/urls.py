from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, CustomAuthToken, WarehouseViewSet,
    ProductViewSet, SupplyView, TakeView
)

router = DefaultRouter()
router.register(r'warehouses', WarehouseViewSet)
router.register(r'products', ProductViewSet)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomAuthToken.as_view(), name='login'),
    path('supply/', SupplyView.as_view(), name='supply'),
    path('take/', TakeView.as_view(), name='take'),
    path('', include(router.urls)),
]
