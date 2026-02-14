from django.shortcuts import render
from django.shortcuts import get_object_or_404

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, viewsets, permissions
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.generics import CreateAPIView

from .models import Warehouse, Product, Stock
from .serializers import (
    RegisterSerializer, WarehouseSerializer, ProductSerializer,
    StockSerializer, SupplySerializer, TakeSerializer
)

# Create your views here.
class RegisterView(CreateAPIView):
    permission_classes = [permissions.AllowAny]
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        token = Token.objects.create(user=user)
        return Response({'token': token.key}, status=status.HTTP_201_CREATED)

class CustomAuthToken(ObtainAuthToken):
    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user_type': user.user_type
        })


class WarehouseViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = WarehouseSerializer
    queryset = Warehouse.objects.all()

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ProductViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ProductSerializer
    queryset = Product.objects.all()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class SupplyView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request):
        if request.user.user_type != 'supplier':
            return Response({"error": "Только поставщики могут поставлять товар"},
                          status=status.HTTP_403_FORBIDDEN)

        serializer = SupplySerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        warehouse = get_object_or_404(Warehouse, id=serializer.validated_data['warehouse_id'])
        product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
        quantity = serializer.validated_data['quantity']

        stock, _ = Stock.objects.get_or_create(
            warehouse=warehouse, product=product, defaults={'quantity': 0}
        )
        stock.quantity += quantity
        stock.save()

        return Response(StockSerializer(stock).data, status=status.HTTP_200_OK)


class TakeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        if request.user.user_type != 'consumer':
            return Response({"error": "Только потребители могут забирать товар"},
                          status=status.HTTP_403_FORBIDDEN)

        serializer = TakeSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        warehouse = get_object_or_404(Warehouse, id=serializer.validated_data['warehouse_id'])
        product = get_object_or_404(Product, id=serializer.validated_data['product_id'])
        quantity = serializer.validated_data['quantity']

        stock = get_object_or_404(Stock, warehouse=warehouse, product=product)

        if stock.quantity < quantity:
            return Response({"error": "Недостаточно товара на складе"},
                          status=status.HTTP_400_BAD_REQUEST)

        stock.quantity -= quantity
        stock.save()

        return Response(StockSerializer(stock).data, status=status.HTTP_200_OK)
