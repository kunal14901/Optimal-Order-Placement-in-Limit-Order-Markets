# Smart-Order-Router ― Trial Task

This repo contains a **stand-alone back-test** of a static Cont–Kukanov Smart
Order Router (SOR) for a 5 000-share parent order, benchmarked against three
baselines (best-ask, TWAP, VWAP).

## Files
| File | Purpose |
|------|---------|
| `backtest.py` | Loads *l1_day.csv*, runs a 50-iteration parameter search, prints JSON with all results, and saves `results.png` (bar chart of average execution price). Imports **only** `json`, `datetime`, `numpy`, `pandas`, and `matplotlib.pyplot`. |
| `results.png` | Example output plot (optional artefact). |
| `results.json` | Example run-output captured from stdout (optional artefact). |
| `README.md` | This document. |

## Quick start
## Suggested Improvement

To further improve fill realism, add queue position modeling using historical fill probabilities for each venue. This would allow the allocator to better estimate the likelihood of limit order fills and adjust allocations dynamically based on observed queue dynamics.
```bash
pip install numpy pandas matplotlib       # ≈ 25 s on a clean venv
python backtest.py                        # prints JSON, writes results.png
