import json
from datetime import datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


# ----------------------------------------------------------------------
# Fee / rebate look-ups  ------------------------------------------------

FEE_MAP = {
    2: 0.0030,   # NASDAQ 
    1: 0.0025    # NYSE    
}

REBATE_MAP = {
    2: 0.0020,
    1: 0.0018
}


def get_fee(pub_id: int) -> float:
    """Return taker fee in $/share for a given publisher_id."""
    return FEE_MAP.get(int(pub_id), 0.0030)


def get_rebate(pub_id: int) -> float:
    """Return maker rebate in $/share for a given publisher_id."""
    return REBATE_MAP.get(int(pub_id), 0.0020)


# ----------------------------------------------------------------------
# Static allocator (exactly as allocator_pseudocode)  ------------------

def allocate(order_size: int,
             venues: list[dict],
             lambda_over: float,
             lambda_under: float,
             theta_queue: float) -> tuple[list[int], float]:
    """
    Exhaustively search 100-share grid for best split across N venues.
    Returns (best_split, best_cost).
    """
    step = 100
    splits: list[list[int]] = [[]]  # start with an empty allocation

    for v in range(len(venues)):
        new_splits: list[list[int]] = []
        for alloc in splits:
            used = sum(alloc)
            max_v = min(order_size - used, venues[v]['ask_size'])
            for q in range(0, max_v + 1, step):
                new_splits.append(alloc + [q])
        splits = new_splits

    best_cost = float('inf')
    best_split: list[int] = []

    for alloc in splits:
        if sum(alloc) != order_size:
            continue
        cost = compute_cost(
            alloc, venues, order_size, lambda_over, lambda_under, theta_queue
        )
        if cost < best_cost:
            best_cost = cost
            best_split = alloc

    return best_split, best_cost


def compute_cost(split: list[int],
                 venues: list[dict],
                 order_size: int,
                 lambda_o: float,
                 lambda_u: float,
                 theta: float) -> float:
    """
    Expected cost of one candidate split (single snapshot).
    """
    executed = 0
    cash_spent = 0.0

    for i, venue in enumerate(venues):
        exe = min(split[i], venue['ask_size'])
        executed += exe
        cash_spent += exe * (venue['ask'] + venue['fee'])

        maker_rebate = max(split[i] - exe, 0) * venue['rebate']
        cash_spent -= maker_rebate

    underfill = max(order_size - executed, 0)
    overfill = max(executed - order_size, 0)

    # θ penalises total mis-execution linearly
    exec_risk = theta * (underfill + overfill)

    # λ penalties
    cost_penalty = lambda_u * underfill + lambda_o * overfill

    return cash_spent + exec_risk + cost_penalty


# ----------------------------------------------------------------------
# Back-test loop  ------------------------------------------------------

def backtest(snapshots: pd.DataFrame,
             params: tuple[float, float, float],
             order_size: int = 5_000) -> float:
    """
    Replay snapshots chronologically, using allocate() at each step until the
    order is filled or we run out of data. Returns *total* cash outlay incl.
    penalties for any residual mis-execution.
    """
    lambda_over, lambda_under, theta_queue = params
    total_executed = 0
    total_cash = 0.0

    for ts, snap in snapshots.groupby('ts_event', sort=True):
        if total_executed >= order_size:
            break

        venues = [{
            'ask': float(row.ask_px_00),
            'ask_size': int(row.ask_sz_00),
            'fee': get_fee(row.publisher_id),
            'rebate': get_rebate(row.publisher_id)
        } for _, row in snap.iterrows()]

        remaining = order_size - total_executed
        alloc, _ = allocate(
            remaining, venues,
            lambda_over, lambda_under, theta_queue
        )

        executed = 0
        cash_spent = 0.0
        rebates = 0.0

        for i, shares in enumerate(alloc):
            exe = min(shares, venues[i]['ask_size'])
            price = venues[i]['ask'] + venues[i]['fee']
            cash_spent += exe * price
            rebates += (shares - exe) * venues[i]['rebate']
            executed += exe

        total_cash += cash_spent - rebates
        total_executed += executed

    # final penalties
    underfill = max(order_size - total_executed, 0)
    overfill = max(total_executed - order_size, 0)
    penalty = (lambda_under * underfill
               + lambda_over * overfill
               + theta_queue * (underfill + overfill))
    return total_cash + penalty


# ----------------------------------------------------------------------
# Simple baselines  ----------------------------------------------------

def best_ask_strategy(snapshots: pd.DataFrame, order_size: int = 5_000) -> float:
    """Always cross the best displayed ask."""
    remaining = order_size
    total_cost = 0.0

    for ts, snap in snapshots.groupby('ts_event', sort=True):
        if remaining <= 0:
            break

        best_venue = None
        best_ask = float('inf')

        for _, row in snap.iterrows():
            if row.ask_px_00 < best_ask:
                best_ask = row.ask_px_00
                best_venue = {
                    'ask': row.ask_px_00,
                    'ask_size': row.ask_sz_00,
                    'fee': get_fee(row.publisher_id)
                }

        if best_venue:
            execute = min(remaining, best_venue['ask_size'])
            total_cost += execute * (best_venue['ask'] + best_venue['fee'])
            remaining -= execute

    return total_cost


def twap_strategy(snapshots: pd.DataFrame,
                  order_size: int = 5_000,
                  bucket_seconds: int = 60) -> float:
    sorted_snaps = snapshots.sort_values('ts_event')
    start_time   = sorted_snaps['ts_event'].min()
    end_time     = sorted_snaps['ts_event'].max()

    n_buckets          = int(np.ceil((end_time - start_time).total_seconds()
                                     / bucket_seconds))
    shares_per_bucket  = order_size / n_buckets
    remaining          = order_size
    total_cost         = 0.0

    for b in range(n_buckets):
        if remaining <= 0:
            break
        bucket_start = start_time + pd.Timedelta(seconds=b * bucket_seconds)
        bucket_end   = bucket_start + pd.Timedelta(seconds=bucket_seconds)

        bucket = sorted_snaps[
            (sorted_snaps.ts_event >= bucket_start) &
            (sorted_snaps.ts_event <  bucket_end)
        ]
        if bucket.empty:
            continue

        row = bucket.iloc[0]
        exec_qty = min(shares_per_bucket, row.ask_sz_00, remaining)
        price    = row.ask_px_00 + get_fee(row.publisher_id)
        total_cost += exec_qty * price
        remaining  -= exec_qty

    # ---------- finish any leftover shares ----------
    if remaining > 0:
        for ts, snap in sorted_snaps.groupby('ts_event', sort=True):
            best_row = snap.loc[snap.ask_px_00.idxmin()]
            exec_qty = min(remaining, best_row.ask_sz_00)
            price    = best_row.ask_px_00 + get_fee(best_row.publisher_id)
            total_cost += exec_qty * price
            remaining  -= exec_qty
            if remaining == 0:
                break

    return total_cost



def vwap_strategy(snapshots: pd.DataFrame, order_size: int = 5_000) -> float:
    """Volume-weighted average across venues each timestamp."""
    remaining = order_size
    total_cost = 0.0

    for ts, snap in snapshots.groupby('ts_event', sort=True):
        if remaining <= 0:
            break

        total_depth = snap.ask_sz_00.sum()
        if total_depth == 0:
            continue

        for _, row in snap.iterrows():
            if remaining <= 0:
                break
            weight = row.ask_sz_00 / total_depth
            target = weight * remaining
            execute = min(target, row.ask_sz_00, remaining)
            price = row.ask_px_00 + get_fee(row.publisher_id)
            total_cost += execute * price
            remaining -= execute

    return total_cost


# ----------------------------------------------------------------------
# Parameter search  ----------------------------------------------------

def parameter_search(snapshots: pd.DataFrame,
                     max_iter: int = 50) -> tuple[tuple[float, float, float], float]:
    """Random search + a tiny deterministic follow-up grid."""
    lambda_over_range = [0.001, 0.005, 0.01, 0.05, 0.1]
    lambda_under_range = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    theta_queue_range = [0.0001, 0.0005, 0.001, 0.005, 0.01]

    best_params = None
    best_cost = float('inf')

    rng = np.random.default_rng(42)

    for i in range(max_iter):
        lo = rng.choice(lambda_over_range)
        lu = rng.choice(lambda_under_range)
        tq = rng.choice(theta_queue_range)

        cost = backtest(snapshots, (lo, lu, tq))

        if cost < best_cost:
            best_cost = cost
            best_params = (lo, lu, tq)

        if (i + 1) % 10 == 0:
            print(f"Iteration {i + 1}/{max_iter} – best cost so far: {best_cost:.2f}")

    # deterministic refinement
    for params in [
        best_params,
        (0.01, 0.5, 0.005),   # empirical mix
        (0.05, 0.1, 0.001)    # risk-averse
    ]:
        cost = backtest(snapshots, params)
        if cost < best_cost:
            best_cost = cost
            best_params = params

    return best_params, best_cost


# ----------------------------------------------------------------------
# Utility  -------------------------------------------------------------

def bps(optimal: float, baseline: float) -> float:
    """Return savings in basis points vs baseline."""
    return (baseline - optimal) / optimal * 10_000


# ----------------------------------------------------------------------
# Main entry-point  ----------------------------------------------------

def main() -> None:
    df = pd.read_csv('l1_day.csv', header=0)

    # --- type conversions -------------------------------------------------
    numeric_cols = df.columns.difference(['ts_event', 'ts_recv'])
    df[numeric_cols] = df[numeric_cols].apply(pd.to_numeric, errors='coerce')
    df.dropna(subset=['ask_px_00', 'ask_sz_00', 'publisher_id', 'ts_event'], inplace=True)

    df['ts_event'] = pd.to_datetime(df['ts_event'])
    df['ts_recv'] = pd.to_datetime(df['ts_recv'], errors='coerce')

    # Build L1 snapshots (first update per publisher per timestamp)
    snapshots = (df.sort_values('ts_event')
                   .groupby(['ts_event', 'publisher_id'])
                   .first()
                   .reset_index())

    # --- optimisation -----------------------------------------------------
    best_params, best_cost = parameter_search(snapshots)

    # --- baselines ---------------------------------------------------------
    ba_cost = best_ask_strategy(snapshots)
    twap_cost = twap_strategy(snapshots)
    vwap_cost = vwap_strategy(snapshots)

    # --- results -----------------------------------------------------------
    results = {
        "best_parameters": {
            "lambda_over": float(best_params[0]),
            "lambda_under": float(best_params[1]),
            "theta_queue": float(best_params[2])
        },
        "optimal_strategy": {
            "total_cost": float(best_cost),
            "avg_price": float(best_cost / 5_000)
        },
        "baselines": {
            "best_ask": {
                "total_cost": float(ba_cost),
                "avg_price": float(ba_cost / 5_000)
            },
            "twap": {
                "total_cost": float(twap_cost),
                "avg_price": float(twap_cost / 5_000)
            },
            "vwap": {
                "total_cost": float(vwap_cost),
                "avg_price": float(vwap_cost / 5_000)
            }
        },
        "savings_bps": {
            "vs_best_ask": bps(best_cost, ba_cost),
            "vs_twap": bps(best_cost, twap_cost),
            "vs_vwap": bps(best_cost, vwap_cost)
        }
    }

    print(json.dumps(results, indent=2))

    # --- simple plot -------------------------------------------------------
    plt.figure(figsize=(8, 5))
    labels = ['Optimal', 'Best Ask', 'TWAP', 'VWAP']
    prices = [
        results["optimal_strategy"]["avg_price"],
        results["baselines"]["best_ask"]["avg_price"],
        results["baselines"]["twap"]["avg_price"],
        results["baselines"]["vwap"]["avg_price"]
    ]
    plt.bar(labels, prices)
    plt.ylabel('Average Price ($)')
    plt.title('Execution Price Comparison')
    plt.savefig('results.png', dpi=120, bbox_inches='tight')
    return results
    


if __name__ == '__main__':
    main()            

