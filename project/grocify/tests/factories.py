"""
Test data factories for Grocify models.
"""
import factory
from decimal import Decimal
from django.contrib.auth.models import User
from datetime import datetime, date

from inventory.models import Category, Supplier, Location, Product, InventoryItem
from customers.models import Customer
from loyalty.models import LoyaltyTier, LoyaltyProfile
from sales.models import SaleTransaction, SaleItem
from purchases.models import PurchaseOrder, PurchaseItem
from credit.models import CreditSale


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_active = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Faker('word')
    description = factory.Faker('text', max_nb_chars=100)
    is_active = True


class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    name = factory.Faker('company')
    contact_person = factory.Faker('name')
    phone = factory.Faker('phone_number')
    email = factory.Faker('email')
    address = factory.Faker('address')
    is_active = True


class LocationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Location

    name = factory.Faker('city')
    address = factory.Faker('address')
    is_active = True


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    name = factory.Faker('word')
    company = factory.Faker('company')
    sku = factory.Sequence(lambda n: f"SKU{n:06d}")
    category = factory.SubFactory(CategoryFactory)
    supplier = factory.SubFactory(SupplierFactory)
    purchase_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True, min_value=Decimal('0.01'))
    selling_price = factory.LazyAttribute(lambda obj: obj.purchase_price * Decimal('1.3'))
    tax_percent = Decimal('10.0')
    reorder_level = 10
    unit = 'pcs'
    is_active = True


class InventoryItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InventoryItem

    product = factory.SubFactory(ProductFactory)
    location = factory.SubFactory(LocationFactory)
    qty_on_hand = factory.Faker('random_int', min=0, max=100)


class LoyaltyTierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoyaltyTier

    name = factory.Iterator(['Bronze', 'Silver', 'Gold', 'Platinum'])
    minimum_points = factory.Faker('random_int', min=0, max=1000, step=100)
    multiplier = factory.Faker('pydecimal', left_digits=1, right_digits=2, positive=True, min_value=Decimal('1.0'), max_value=Decimal('2.0'))


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Faker('name')
    phone = factory.Sequence(lambda n: f"123456{n:04d}")
    email = factory.Faker('email')
    address = factory.Faker('address')
    outstanding_balance = Decimal('0.00')
    points = factory.Faker('random_int', min=0, max=1000)
    tier = factory.SubFactory(LoyaltyTierFactory)
    is_active = True


class LoyaltyProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = LoyaltyProfile

    customer = factory.SubFactory(CustomerFactory)
    points = factory.Faker('random_int', min=0, max=1000)
    tier = factory.SubFactory(LoyaltyTierFactory)


class SaleTransactionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SaleTransaction

    invoice_number = factory.Sequence(lambda n: f"INV-{datetime.now().strftime('%Y%m%d')}-{n:06d}")
    cashier = factory.SubFactory(UserFactory)
    customer = factory.SubFactory(CustomerFactory)
    location = factory.SubFactory(LocationFactory)
    payment_method = 'Cash'
    subtotal = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    total_amount = factory.LazyAttribute(lambda obj: obj.subtotal)
    amount_paid = factory.LazyAttribute(lambda obj: obj.total_amount)
    change_due = Decimal('0.00')
    discount_amount = Decimal('0.00')
    points_earned = 0
    points_redeemed = 0


class SaleItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SaleItem

    transaction = factory.SubFactory(SaleTransactionFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('pydecimal', left_digits=2, right_digits=2, positive=True, min_value=Decimal('1.0'))
    price_at_sale = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    discount_amount = Decimal('0.00')


class PurchaseOrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseOrder

    supplier = factory.SubFactory(SupplierFactory)
    location = factory.SubFactory(LocationFactory)
    date_ordered = factory.Faker('date_this_year')
    status = 'Pending'
    notes = factory.Faker('text', max_nb_chars=100)


class PurchaseItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PurchaseItem

    purchase_order = factory.SubFactory(PurchaseOrderFactory)
    product = factory.SubFactory(ProductFactory)
    quantity = factory.Faker('random_int', min=1, max=100)
    cost_price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)


class CreditSaleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CreditSale

    customer = factory.SubFactory(CustomerFactory)
    credit_amount = factory.Faker('pydecimal', left_digits=4, right_digits=2, positive=True)
    issued_on = factory.Faker('date_time_this_year')
    due_date = factory.Faker('date_between', start_date='+1d', end_date='+30d')
    is_settled = False
    location = factory.SubFactory(LocationFactory)
    reference_number = factory.Sequence(lambda n: f"CR-{n:06d}")
    notes = factory.Faker('text', max_nb_chars=100)