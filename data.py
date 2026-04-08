import pandas as pd
import numpy as np


def finalize_df_metrics(df):
    """Standardizes runway math and net burn for both modes."""
    df["net_burn"] = df["burn"] - df["revenue"]

    def calc_runway(row):
        # Default Alive: profitable or breakeven → cap at 5 years
        if row["net_burn"] <= 0:
            return 5.0
        # Avoid division by very small numbers causing explosions
        if row["net_burn"] < 1:
            return 5.0
        runway_months = row["cash_on_hand"] / row["net_burn"]
        # Hard cap at 5 years (60 months) regardless
        return round(min(runway_months / 12, 5.0), 2)

    df["runway_years"] = df.apply(calc_runway, axis=1)
    return df


def generate_startup_data():
    """Demo Mode: Synthetic 24-month B2B SaaS story."""
    months = list(range(1, 25))
    rev = [20000 * (1.05**m if m < 8 else 1.12**m) for m in months]
    burn = [120000 + (5000 * m) for m in months]
    for m in [6, 12, 18]:
        burn[m - 1:] = [b + 20000 for b in burn[m - 1:]]

    funding = [0] * 24
    funding[11] = 5_000_000  # Series A at month 12

    cash = []
    curr_cash = 1_500_000
    for m in range(24):
        curr_cash = curr_cash - burn[m] + rev[m] + funding[m]
        cash.append(max(curr_cash, 0))

    df = pd.DataFrame({
        "month": months,
        "revenue": rev,
        "burn": burn,
        "cash_on_hand": cash,
        "funding_event": funding,
    })
    return finalize_df_metrics(df)


def generate_custom_data(cash_start, rev_start, burn_start, growth_rate=0.10):
    """Manual Entry: Projects 24 months from real founder inputs."""
    months = list(range(1, 25))
    revs = []
    curr_rev = rev_start
    for _ in months:
        revs.append(round(curr_rev))
        curr_rev *= (1 + growth_rate)

    burns = [int(burn_start)] * 24
    cash_on_hand = []
    curr_cash = cash_start
    for m in range(24):
        curr_cash = curr_cash - burns[m] + revs[m]
        cash_on_hand.append(max(curr_cash, 0))

    df = pd.DataFrame({
        "month": months,
        "revenue": revs,
        "burn": burns,
        "cash_on_hand": cash_on_hand,
        "funding_event": [0] * 24,
    })
    return finalize_df_metrics(df)


def apply_scenario(df, rev_change, burn_change):
    """
    Applies % shifts to revenue and burn, then recalculates cash from scratch.
    Reconstructs starting cash from the first row so it works for both
    Demo Mode and Manual Entry without any hardcoded values.
    """
    df2 = df.copy()
    df2["revenue"] = (df2["revenue"] * (1 + rev_change)).astype(int)
    df2["burn"] = (df2["burn"] * (1 + burn_change)).astype(int)

    # Reverse-engineer starting cash from row 0 of the original df
    first = df.iloc[0]
    starting_cash = first["cash_on_hand"] + first["burn"] - first["revenue"] - first["funding_event"]

    curr_cash = starting_cash
    new_cash = []
    for _, row in df2.iterrows():
        curr_cash = curr_cash + row["funding_event"] - row["burn"] + row["revenue"]
        new_cash.append(max(curr_cash, 0))

    df2["cash_on_hand"] = new_cash
    return finalize_df_metrics(df2)