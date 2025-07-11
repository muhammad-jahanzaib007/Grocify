from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import CreditSale, CreditPayment
from customers.models import Customer

@receiver(post_save, sender=CreditSale)
def update_customer_balance_on_sale(sender, instance, created, **kwargs):
    if created:
        customer = instance.customer
        customer.pending_balance += instance.amount
        customer.save()
@property
def is_overdue(self):
    from django.utils import timezone
    return not self.is_settled and self.due_date < timezone.now().date()

@receiver(post_save, sender=CreditPayment)
def update_customer_balance_on_payment(sender, instance, created, **kwargs):
    if created:
        customer = instance.customer
        customer.pending_balance -= instance.amount_paid
        customer.pending_balance = max(customer.pending_balance, 0)  # Avoid negatives
        customer.save()