from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import CreditSale, CreditPayment

@receiver(post_save, sender=CreditSale)
def recalc_outstanding_on_credit_sale(sender, instance, created, **kwargs):
    """
    Whenever a CreditSale is created or updated, recalculate
    the customer's outstanding balance.
    """
    instance.customer.recalculate_outstanding()


@receiver(post_save, sender=CreditPayment)
def apply_payment_to_credit_sale(sender, instance, created, **kwargs):
    """
    When a new payment is recorded, add it to the related CreditSale
    so that amount_paid and is_settled update via its save() hook.
    """
    if not created:
        return

    sale = instance.credit_sale
    sale.amount_paid += instance.amount_paid
    sale.save()