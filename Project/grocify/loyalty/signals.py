from django.db.models.signals import post_save
from django.dispatch import receiver
from sales.models import SaleTransaction
from loyalty.models import LoyaltyProfile, PointTransaction
from customers.models import Customer
from loyalty.utils import calculate_earned_points

@receiver(post_save, sender=SaleTransaction)
def award_loyalty_points(sender, instance, created, **kwargs):
    if not created:
        return  # Only award points on first-time save

    customer = instance.customer
    if not customer or customer.phone == '0000000000':
        return  # Skip Walk-In or empty customer

    # Create or fetch loyalty profile
    profile, _ = LoyaltyProfile.objects.get_or_create(customer=customer)

    # Calculate earned points using tier multiplier
    current_tier_name = profile.tier.name if profile.tier else None
    earned_points = calculate_earned_points(float(instance.total_amount), current_tier_name)

    # Update profile
    profile.points += earned_points
    profile.lifetime_points += earned_points
    profile.save()  # triggers tier sync + customer summary

    # Log point transaction
    PointTransaction.objects.create(
        profile=profile,
        points=earned_points,
        transaction_type='earned',
        source=f"Sale #{instance.invoice_number}",
        note='Auto-awarded from completed sale'
    )