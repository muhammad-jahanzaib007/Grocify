from django.db.models.signals import post_save
from django.dispatch import receiver
from sales.models import Sale
from loyalty.models import LoyaltyProfile, PointTransaction
from customers.models import Customer

@receiver(post_save, sender=Sale)
def award_loyalty_points(sender, instance, created, **kwargs):
    if not created:
        return  # Only award points on first-time save

    customer = instance.customer
    if not customer:
        return  # No customer attached — skip

    # Calculate earned points (e.g. 5% of sale amount)
    earned_points = int(instance.total_amount * 0.05)  # Customize %

    # Create or fetch loyalty profile
    profile, _ = LoyaltyProfile.objects.get_or_create(customer=customer)

    # Update profile
    profile.points += earned_points
    profile.lifetime_points += earned_points
    profile.save()

    # Record transaction
    PointTransaction.objects.create(
        profile=profile,
        points=earned_points,
        transaction_type='earned',
        source=f"Sale #{instance.id}",
        note='Auto-awarded from completed sale'
    )