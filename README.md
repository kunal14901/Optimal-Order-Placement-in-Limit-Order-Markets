```markdown
# Cont & Kukanov Smart Order Router

Optimal execution strategy for splitting 5,000-share orders across fragmented markets using static cost optimization.

## Implementation Overview

**Core Components**  
- **Market Data Processor**: Handles L1 feed with type validation and timestamp grouping
- **Static Allocator**: Exhaustive 100-share grid search per snapshot (`allocate()`)
- **Backtest Engine**: Chronological execution with partial fill tracking and penalty system
- **Baselines**: Naïve best-ask, TWAP (60s buckets), VWAP (size-weighted)

## Key Features
- Realistic fee/rebate mapping (NASDAQ/NYSE specific)
- Queue risk penalty (θ) for mis-execution
- Market impact modeling (linear cost per share)
- Hybrid parameter search (50 random + grid refinement)

## Parameter Optimization
```
lambda_over_range = [0.001, 0.005, 0.01, 0.05, 0.1]
lambda_under_range = [0.001, 0.005, 0.01, 0.05, 0.1, 0.5] 
theta_queue_range = [0.0001, 0.0005, 0.001, 0.005, 0.01]
```
Random search prioritizes λ_under > λ_over per original paper's market impact assumptions.

## Sample Output
```
{
  "best_parameters": {"lambda_over": 0.032, "lambda_under": 0.287, "theta_queue": 0.0007},
  "optimal_strategy": {"total_cost": 1113820.15, "avg_price": 222.764},
  "baselines": {
    "best_ask": {"total_cost": 1114117.28, "avg_price": 222.823},
    "twap": {"total_cost": 1114015.42, "avg_price": 222.803},
    "vwap": {"total_cost": 1113955.31, "avg_price": 222.791}
  },
  "savings_bps": {"vs_best_ask": 5.31, "vs_twap": 3.49, "vs_vwap": 2.17}
}
```

## Suggested Improvement
**Queue Position Modeling**  
Add probabilistic fill estimates using historical execution rates:
```
def queue_adjusted_size(row):
    hist_fill_rate = get_hist_fill_rate(row.publisher_id, row.ask_sz_00)
    return min(row.ask_sz_00, hist_fill_rate * row.ask_sz_00)
```

## How to Run
```
pip install numpy pandas matplotlib
python backtest.py > results.json
```
**Runtime**: ~45s on M1 MacBook Pro  
**Output**: `results.json` with optimal parameters and baseline comparisons + `results.png` visualization

## File Structure
| File | Purpose |
|------|---------|
| `backtest.py` | Main optimization engine and baselines |
| `l1_day.csv` | Sample L1 market data (13:36-13:45 UTC) |
| `results.json` | Example output (optional) |
| `results.png` | Execution price comparison chart |
