import pandas as pd
import numpy as np


def generate_startup_data(seed: int = 42) -> pd.DataFrame:
    """
    Generate a realistic 24-month synthetic startup dataset.

    Mimics an early-stage B2B SaaS startup:
    - Slow early revenue growth that accelerates after product-market fit
    - Burn rate that gradually increases with hiring
    - A Series A funding event at month 12
    - Cash balance reflecting real dynamics
    """
    np.random.seed(seed)
    n_months = 24

    months = list(range(1, n_months + 1))

    # --- Revenue: starts small, accelerates with noise ---
    # Growth rate increases after month 8 (PMF inflection)
    base_revenue = []
    rev = 18_000
    for m in months:
        if m <= 8:
            growth = np.random.uniform(0.04, 0.09)  # 4–9% monthly
        else:
            growth = np.random.uniform(0.08, 0.15)  # 8–15% monthly post-PMF
        rev *= (1 + growth)
        base_revenue.append(round(rev))

    # --- Burn: starts at ~$120k/mo, slowly climbs with headcount ---
    base_burn = []
    burn = 120_000
    for m in months:
        # Hiring events at months 6, 12, 18
        if m in [6, 12, 18]:
            burn *= np.random.uniform(1.10, 1.18)  # +10–18% on hiring months
        else:
            burn *= np.random.uniform(1.005, 1.015)  # small creep
        base_burn.append(round(burn))

    # --- Headcount: grows step-wise ---
    headcount = []
    hc = 5
    for m in months:
        if m in [4, 6, 9, 12, 15, 18, 21]:
            hc += np.random.randint(1, 4)
        headcount.append(hc)

    # --- Funding events ---
    # Seed round already in bank at month 1 ($1.5M)
    # Series A at month 12 ($5M)
    funding_events = [0] * n_months
    funding_events[11] = 5_000_000  # Series A at month 12

    # --- Cash on hand ---
    cash = 1_500_000  # Starting cash (post-seed)
    cash_on_hand = []
    for m in range(n_months):
        cash += funding_events[m]
        cash -= base_burn[m]
        cash += base_revenue[m]
        cash_on_hand.append(max(cash, 0))  # no negative cash for now

    df = pd.DataFrame({
        "month": months,
        "revenue": base_revenue,
        "burn": base_burn,
        "cash_on_hand": cash_on_hand,
        "headcount": headcount,
        "funding_event": funding_events,
    })

    # Derived
    df["net_burn"] = df["burn"] - df["revenue"]
    df["runway_months"] = (df["cash_on_hand"] / df["net_burn"].clip(lower=1)).round(1)

    return df


def apply_scenario(df: pd.DataFrame, rev_change: float, burn_change: float) -> pd.DataFrame:
    """
    Apply percentage changes to revenue and burn across the full dataset.
    Recalculates cash and runway from scratch.

    Args:
        df: Original dataset
        rev_change: Revenue multiplier delta, e.g. 0.10 = +10%
        burn_change: Burn multiplier delta, e.g. -0.15 = -15%

    Returns:
        New dataframe with adjusted figures
    """
    df2 = df.copy()
    df2["revenue"] = (df2["revenue"] * (1 + rev_change)).round(0).astype(int)
    df2["burn"] = (df2["burn"] * (1 + burn_change)).round(0).astype(int)

    # Recalculate cash from scratch
    cash = 1_500_000
    new_cash = []
    for _, row in df2.iterrows():
        cash += row["funding_event"]
        cash -= row["burn"]
        cash += row["revenue"]
        new_cash.append(max(cash, 0))

    df2["cash_on_hand"] = new_cash
    df2["net_burn"] = df2["burn"] - df2["revenue"]
    df2["runway_months"] = (df2["cash_on_hand"] / df2["net_burn"].clip(lower=1)).round(1)

    return df2
