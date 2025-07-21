"""
Critical view tests for authentication and business logic.
"""
import json
from decimal import Decimal
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.contrib.messages import get_messages

from .factories import (
    UserFactory, ProductFactory, CustomerFactory, LocationFactory,
    InventoryItemFactory, SaleTransactionFactory, PurchaseOrderFactory
)
from sales.models import SaleTransaction
from purchases.models import PurchaseOrder


class AuthenticationTestCase(TestCase):
    """Test authentication requirements for protected views."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()

    def test_purchases_dashboard_requires_login(self):
        """Test that purchases dashboard requires authentication."""
        response = self.client.get('/purchases/')
        self.assertRedirects(response, '/users/login/?next=/purchases/')

    def test_customers_dashboard_requires_login(self):
        """Test that customers dashboard requires authentication."""
        response = self.client.get('/customers/')
        self.assertRedirects(response, '/users/login/?next=/customers/')

    def test_api_endpoint_requires_login(self):
        """Test that API endpoints require authentication."""
        response = self.client.get('/api/products/search/')
        self.assertRedirects(response, '/users/login/?next=/api/products/search/')

    def test_authenticated_access_works(self):
        """Test that authenticated users can access protected views."""
        self.client.force_login(self.user)
        
        # These should not redirect to login
        response = self.client.get('/purchases/')
        self.assertNotEqual(response.status_code, 302)


class PurchasesViewTest(TestCase):
    """Test purchases-related views."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.location = LocationFactory()
        self.client.force_login(self.user)

    def test_purchases_dashboard_loads(self):
        """Test purchases dashboard loads correctly."""
        response = self.client.get('/purchases/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Purchases Dashboard')

    def test_purchase_order_creation(self):
        """Test purchase order creation with form."""
        supplier = PurchaseOrderFactory().supplier
        
        data = {
            'supplier': supplier.id,
            'location': self.location.id,
            'date_ordered': '2024-01-01',
            'status': 'Pending',
            'notes': 'Test order'
        }
        
        response = self.client.post('/purchases/create/', data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        self.assertTrue(PurchaseOrder.objects.filter(supplier=supplier).exists())

    def test_purchase_order_list_performance(self):
        """Test that purchase order list doesn't have N+1 queries."""
        # Create test data
        for _ in range(5):
            PurchaseOrderFactory(location=self.location)
        
        with self.assertNumQueries(5):  # Should be limited queries due to select_related
            response = self.client.get('/purchases/list/')
            self.assertEqual(response.status_code, 200)


class SalesViewTest(TestCase):
    """Test sales-related views and critical business logic."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.location = LocationFactory()
        self.customer = CustomerFactory()
        self.product = ProductFactory()
        self.inventory = InventoryItemFactory(
            product=self.product, 
            location=self.location, 
            qty_on_hand=100
        )
        self.client.force_login(self.user)

    def test_pos_sale_processing(self):
        """Test complete POS sale processing workflow."""
        cart_data = [
            {
                'product_id': self.product.id,
                'name': self.product.name,
                'qty': 2,
                'price': float(self.product.selling_price)
            }
        ]
        
        data = {
            'cart': json.dumps(cart_data),
            'payment_method': 'Cash',
            'amount_paid': 100.00,
            'customer_id': self.customer.id,
            'discount_amount': 0,
            'points_used': 0
        }
        
        response = self.client.post('/sales/process/', data)
        self.assertEqual(response.status_code, 302)  # Redirect after success
        
        # Check that sale was created
        self.assertTrue(SaleTransaction.objects.filter(customer=self.customer).exists())
        
        # Check inventory was updated
        self.inventory.refresh_from_db()
        self.assertEqual(self.inventory.qty_on_hand, 98)  # 100 - 2

    def test_insufficient_stock_prevention(self):
        """Test prevention of sales with insufficient stock."""
        # Set low stock
        self.inventory.qty_on_hand = 1
        self.inventory.save()
        
        cart_data = [
            {
                'product_id': self.product.id,
                'name': self.product.name,
                'qty': 5,  # More than available
                'price': float(self.product.selling_price)
            }
        ]
        
        data = {
            'cart': json.dumps(cart_data),
            'payment_method': 'Cash',
            'amount_paid': 100.00,
            'customer_id': self.customer.id,
        }
        
        response = self.client.post('/sales/process/', data)
        
        # Should show error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Not enough stock' in str(m) for m in messages))

    def test_credit_sale_validation(self):
        """Test credit sale validation for walk-in customers."""
        walkin = CustomerFactory(phone='0000000000', name='Walk-In Customer')
        
        cart_data = [
            {
                'product_id': self.product.id,
                'name': self.product.name,
                'qty': 1,
                'price': float(self.product.selling_price)
            }
        ]
        
        data = {
            'cart': json.dumps(cart_data),
            'payment_method': 'Credit',  # Credit not allowed for walk-in
            'amount_paid': 0,
            'customer_id': walkin.id,
        }
        
        response = self.client.post('/sales/process/', data)
        
        # Should show error message
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Credit sales are not allowed' in str(m) for m in messages))


class APIViewTest(TestCase):
    """Test API endpoints."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_product_search_api(self):
        """Test product search API returns correct data."""
        product = ProductFactory(name='Test Product', sku='TEST123')
        InventoryItemFactory(product=product, qty_on_hand=50)
        
        response = self.client.get('/api/products/search/?q=Test')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['name'], 'Test Product')
        self.assertEqual(data[0]['stock'], 50)

    def test_product_search_api_aggregates_stock(self):
        """Test that API correctly aggregates stock across locations."""
        product = ProductFactory()
        location1 = LocationFactory()
        location2 = LocationFactory()
        
        InventoryItemFactory(product=product, location=location1, qty_on_hand=30)
        InventoryItemFactory(product=product, location=location2, qty_on_hand=20)
        
        response = self.client.get(f'/api/products/search/?q={product.sku}')
        data = response.json()
        
        self.assertEqual(data[0]['stock'], 50)  # 30 + 20


class CustomersViewTest(TestCase):
    """Test customer-related views."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_customers_dashboard_statistics(self):
        """Test customers dashboard shows correct statistics."""
        # Create test customers
        CustomerFactory.create_batch(5, is_active=True)
        CustomerFactory.create_batch(2, is_active=False)
        
        response = self.client.get('/customers/')
        self.assertEqual(response.status_code, 200)
        
        # Check context data
        self.assertEqual(response.context['total_customers'], 7)
        self.assertEqual(response.context['active_customers'], 5)


class PerformanceTestCase(TestCase):
    """Test performance optimizations."""

    def setUp(self):
        self.client = Client()
        self.user = UserFactory()
        self.client.force_login(self.user)

    def test_purchases_dashboard_query_optimization(self):
        """Test purchases dashboard uses optimized queries."""
        location = LocationFactory()
        
        # Create test data
        for _ in range(10):
            PurchaseOrderFactory(location=location)
        
        with self.assertNumQueries(4):  # Should be minimal due to select_related
            response = self.client.get('/purchases/')
            self.assertEqual(response.status_code, 200)