# ─── TIER CONFIGURATION ─────────────────────────────────────────────────────────
LOYALTY_TIERS = {
    'Bronze': 0,
    'Silver': 1000,
    'Gold': 2500,
    'Platinum': 5000,
}

TIER_MULTIPLIERS = {
    'Bronze': 1.0,
    'Silver': 1.1,
    'Gold': 1.25,
    'Platinum': 1.5,
}


# ─── TIER ASSIGNMENT LOGIC ─────────────────────────────────────────────────────
def get_loyalty_tier(lifetime_points: int) -> str:
    """
    Returns the appropriate tier name based on lifetime points.
    """
    sorted_tiers = sorted(LOYALTY_TIERS.items(), key=lambda x: x[1])
    current_tier = 'Bronze'
    for tier, threshold in sorted_tiers:
        if lifetime_points >= threshold:
            current_tier = tier
        else:
            break
    return current_tier


# ─── POINT CALCULATION ─────────────────────────────────────────────────────────
def calculate_earned_points(sale_amount: float, tier: str = None) -> int:
    """
    Returns earned points from a sale, applying tier multiplier.
    """
    base_rate = 0.05  # 5% back
    multiplier = TIER_MULTIPLIERS.get(tier, 1.0)
    return int(sale_amount * base_rate * multiplier)