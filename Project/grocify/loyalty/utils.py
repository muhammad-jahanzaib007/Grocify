# Loyalty Tier Configuration
LOYALTY_TIERS = {
    'Bronze': 0,
    'Silver': 1000,
    'Gold': 2500,
    'Platinum': 5000,
}

def get_loyalty_tier(lifetime_points: int) -> str:
    """
    Returns the appropriate loyalty tier based on lifetime points.
    """
    sorted_tiers = sorted(LOYALTY_TIERS.items(), key=lambda x: x[1])
    current_tier = 'Bronze'
    for tier, threshold in sorted_tiers:
        if lifetime_points >= threshold:
            current_tier = tier
        else:
            break
    return current_tier


def calculate_earned_points(sale_amount: float, tier: str = None) -> int:
    """
    Calculates how many points should be earned from a sale, 
    optionally applying tier multipliers.
    """
    base_rate = 0.05  # 5% back as points
    tier_multiplier = {
        'Bronze': 1.0,
        'Silver': 1.1,
        'Gold': 1.25,
        'Platinum': 1.5,
    }
    multiplier = tier_multiplier.get(tier, 1.0)
    return int(sale_amount * base_rate * multiplier)