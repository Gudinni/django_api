from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from .models import Warehouse, Product, Stock

User = get_user_model()


class WarehouseAPITestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = '/api/register/'
        self.login_url = '/api/login/'
        self.warehouses_url = '/api/warehouses/'
        self.products_url = '/api/products/'
        self.supply_url = '/api/supply/'
        self.take_url = '/api/take/'

        self.supplier_data = {
            'username': 'supplier',
            'email': 'supplier@example.com',
            'password': 'testpass123',
            'user_type': 'supplier'
        }
        self.consumer_data = {
            'username': 'consumer',
            'email': 'consumer@example.com',
            'password': 'testpass123',
            'user_type': 'consumer'
        }

    def register_user(self, data):
        response = self.client.post(self.register_url, data)
        return response

    def login_user(self, username, password):
        response = self.client.post(self.login_url, {'username': username, 'password': password})
        if response.status_code == 200:
            return response.data['token']
        return None

    def test_register_supplier(self):
        response = self.register_user(self.supplier_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_register_consumer(self):
        response = self.register_user(self.consumer_data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    def test_login(self):
        self.register_user(self.supplier_data)
        token = self.login_user('supplier', 'testpass123')
        self.assertIsNotNone(token)

    def test_create_warehouse_authenticated(self):
        self.register_user(self.supplier_data)
        token = self.login_user('supplier', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {'name': 'Test Warehouse'}
        response = self.client.post(self.warehouses_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Warehouse.objects.count(), 1)

    def test_create_product_authenticated(self):
        self.register_user(self.supplier_data)
        token = self.login_user('supplier', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        data = {'name': 'Test Product'}
        response = self.client.post(self.products_url, data)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Product.objects.count(), 1)

    def test_supply_by_supplier(self):
        self.register_user(self.supplier_data)
        token = self.login_user('supplier', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        warehouse = Warehouse.objects.create(name='Warehouse1', owner=User.objects.get(username='supplier'))
        product = Product.objects.create(name='Product1', creator=User.objects.get(username='supplier'))

        data = {'warehouse_id': warehouse.id, 'product_id': product.id, 'quantity': 10}
        response = self.client.post(self.supply_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stock = Stock.objects.get(warehouse=warehouse, product=product)
        self.assertEqual(stock.quantity, 10)

    def test_supply_by_consumer_forbidden(self):
        self.register_user(self.consumer_data)
        token = self.login_user('consumer', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        warehouse = Warehouse.objects.create(name='Warehouse1', owner=User.objects.get(username='consumer'))
        product = Product.objects.create(name='Product1', creator=User.objects.get(username='consumer'))

        data = {'warehouse_id': warehouse.id, 'product_id': product.id, 'quantity': 10}
        response = self.client.post(self.supply_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_take_by_consumer(self):
        self.register_user(self.supplier_data)
        token_sup = self.login_user('supplier', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_sup}')
        warehouse = Warehouse.objects.create(name='Warehouse1', owner=User.objects.get(username='supplier'))
        product = Product.objects.create(name='Product1', creator=User.objects.get(username='supplier'))
        Stock.objects.create(warehouse=warehouse, product=product, quantity=10)

        self.register_user(self.consumer_data)
        token_con = self.login_user('consumer', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token_con}')

        data = {'warehouse_id': warehouse.id, 'product_id': product.id, 'quantity': 5}
        response = self.client.post(self.take_url, data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        stock = Stock.objects.get(warehouse=warehouse, product=product)
        self.assertEqual(stock.quantity, 5)

    def test_take_by_supplier_forbidden(self):
        self.register_user(self.supplier_data)
        token = self.login_user('supplier', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        warehouse = Warehouse.objects.create(name='Warehouse1', owner=User.objects.get(username='supplier'))
        product = Product.objects.create(name='Product1', creator=User.objects.get(username='supplier'))
        Stock.objects.create(warehouse=warehouse, product=product, quantity=10)

        data = {'warehouse_id': warehouse.id, 'product_id': product.id, 'quantity': 5}
        response = self.client.post(self.take_url, data)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_take_more_than_available(self):
        self.register_user(self.consumer_data)
        token = self.login_user('consumer', 'testpass123')
        self.client.credentials(HTTP_AUTHORIZATION=f'Token {token}')

        warehouse = Warehouse.objects.create(name='Warehouse1', owner=User.objects.get(username='consumer'))
        product = Product.objects.create(name='Product1', creator=User.objects.get(username='consumer'))
        Stock.objects.create(warehouse=warehouse, product=product, quantity=5)

        data = {'warehouse_id': warehouse.id, 'product_id': product.id, 'quantity': 10}
        response = self.client.post(self.take_url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_access(self):
        response = self.client.post(self.warehouses_url, {'name': 'Unauthorized'})
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)