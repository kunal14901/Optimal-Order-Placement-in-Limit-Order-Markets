```markdown
# Cont-Kukanov Smart Order Router Backtest

This repository implements a backtest and optimizer for the Cont & Kukanov static cost model for optimal order placement in fragmented limit order markets. The script splits a 5,000-share buy order across multiple venues to minimize execution costs, using the exact allocator logic from the provided pseudocode.

## Code Structure

- **backtest.py**: Loads `l1_day.csv`, processes L1 market data, implements the static allocator, and runs a 50-iteration parameter search for `lambda_over`, `lambda_under`, and `theta_queue`. It benchmarks the tuned result against three baselines: best-ask, TWAP (60s buckets), and VWAP (weighted by displayed ask size). Outputs a JSON summary and a bar chart (`results.png`).
- **allocator_pseudocode.txt**: The exact static allocation algorithm (do not modify).
- **l1_day.csv**: Mocked L1 market data for backtesting.
- **results.png/results.json**: Example output files (optional).

## Parameter Search

- Random search over:
    - `lambda_over`: [0.001, 0.005, 0.01, 0.05, 0.1]
    - `lambda_under`: [0.001, 0.005, 0.01, 0.05, 0.1, 0.5]
    - `theta_queue`: [0.0001, 0.0005, 0.001, 0.005, 0.01]
- Final candidates are verified deterministically.

## How to Run

```
pip install numpy pandas matplotlib
python backtest.py
```

## Output

- Prints a JSON object with the best parameters, total/average cost for optimal and baseline strategies, and savings in basis points.
- Saves a bar chart of average execution price as `results.png`.

## Suggested Improvement

To further improve fill realism, add queue position modeling using historical fill probabilities for each venue. This would allow the allocator to better estimate the likelihood of limit order fills and adjust allocations dynamically based on observed queue dynamics.

---

*Implementation strictly follows the provided pseudocode and assignment requirements. For details, see allocator_pseudocode.txt and the task description.*
