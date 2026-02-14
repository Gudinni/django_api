from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Warehouse, Product, Stock

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    user_type = serializers.ChoiceField(choices=['supplier', 'consumer'])

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'user_type')

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            user_type=validated_data['user_type']
        )
        return user


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
        read_only_fields = ['owner']


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = '__all__'
        read_only_fields = ['creator']


class StockSerializer(serializers.ModelSerializer):
    class Meta:
        model = Stock
        fields = '__all__'


class SupplySerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)


class TakeSerializer(serializers.Serializer):
    warehouse_id = serializers.IntegerField()
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
