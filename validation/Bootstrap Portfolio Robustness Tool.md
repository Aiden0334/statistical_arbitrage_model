# Bootstrap Portfolio Robustness Tool

A generic tool for testing whether our statistical arbitrage / pair trading / basis trading strategy performance is robust to random pair subsampling, or fragile due to concentration in a few lucky pairs.

## Motivation

Backtest results can look great in aggregate but hide the fact that all the alpha comes from a handful of pairs. If those pairs stop working, the whole portfolio falls. This tool tests robustness by: 

1. Randomly selecting a subset of pairs
2. Computing portfolio metrics on that subset.
3. Repeating N times.
4. Reporting the distribution.

If the 5th percentile Sharpe is still positive, our alpha is well-distributed.

## Input Format

Trade log (Parquet or CSV) with columns:
- `pair`: Pair identifier (or single asset name).
- `net_return`: Per-trade net return (decimal, e.g., 0.02 for +2%).
- `entry_time`: Trade entry timestamp.
- `exit_time`: Trade exit timestamp.

## Usage

```bash
python bootstrap_portfolio_robustness.py \
    --trades my_backtest_trades.parquet \
    --iterations 100 \
    --fraction 0.5
```

## Options
- `--iterations`: Number of bootstrap iterations (default: 100).
- `--fraction`: Fraction of pairs to sample each iteration (default: 0.5).
- `--capital`: Initial capital for equity calculation (default: 100,000).
- `--output`: Save iteration results to file.

## Interpretation

| 5% Percentile Sharpe | Verdict |
|---|---|
| > 0.5 | Robust — alpha well-distributed |
| 0 to 0.5 | Acceptable but concentrated |
| < 0 | Fragile — depends on lucky pairs |

## License
MIT
