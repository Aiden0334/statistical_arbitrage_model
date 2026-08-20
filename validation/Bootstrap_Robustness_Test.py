"""
Bootstrap Pair Robustness Test.

목적:
    48 pair 중 랜덤 subset으로 backtest 반복.
    Sharpe distribution 확인 → 특정 pair 의존도 검증.

방법:
    100회 반복:
        - 48 pair 중 24 pair 랜덤 선택 (50%).
        - IS 통계로 OOS 2026 backtest.
        - Sharpe, MDD, Return 기록.
    Distribution 통계 (median, percentiles) 출력.

판정:
    - 5% percentile Sharpe > 0.5: robust.
    - 5% percentile < 0: fragile.
"""
import sys
sys.path.append('Local_Path2')

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from joblib import Parallel, delayed
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("My_Local_Path")
REGIME_DIR = DATA_DIR / "regimes1"
BACKTEST_DIR = DATA_DIR / "results1"

#-----------------------------------------------------------------------------------------------------------
# Config
# Parameters are erased due to copyright issues.
#-----------------------------------------------------------------------------------------------------------

IS_START = pd.Timestamp('2020-01-01', tz='UTC')
IS_END = pd.Timestamp('2026-01-01', tz='UTC')
OOS_START = pd.Timestamp('2026-01-01', tz='UTC')
OOS_END = pd.Timestamp('2026-08-01', tz='UTC')

# Bootstrap
N_ITERATIONS = 100
PAIR_FRACTION = 0.5  # 50% pair 선택


def load_price(symbol):
    path = DATA_DIR / f"futures_um_{symbol}_{TF}.parquet"
    df = pd.read_parquet(path)
    if 'open_time' in df.columns:
        df = df.set_index('open_time')
    df.index = pd.to_datetime(df.index, utc=True)
    return df['close']


def load_funding(symbol):
    path = DATA_DIR / f"funding_{symbol}.parquet"
    if not path.exists():
        return None
    df = pd.read_parquet(path)
    df = df.set_index('calc_time')
    return df['funding_rate']


def load_spread_regime(pair_name):
    # Path in my local computer is excluded due to copyright issue.

def ols_hedge(p1_log, p2_log):
    X = add_constant(p2_log)
    model = OLS(p1_log, X).fit()
    return model.params.iloc[1], model.params.iloc[0]


def compute_funding_pnl(n1, n2, x1, x2, x3):
    # logic is erased due to copyright issue.

def get_spread_allow(timestamp, regime_df):
    # logic is erased due to copyright issue.

def backtest_pair(pair_row):
    """한 pair OOS backtest."""
    s1 = pair_row['symbol_1']
    s2 = pair_row['symbol_2']
    pair_name = f"{s1}_{s2}"
    
    try:
        p1 = load_price(s1)
        p2 = load_price(s2)
    except:
        return None
    
    common = p1.dropna().index.intersection(p2.dropna().index)
    p1 = p1.loc[common]
    p2 = p2.loc[common]
    
    is_mask = (p1.index >= IS_START) & (p1.index < IS_END)
    oos_mask = (p1.index >= OOS_START) & (p1.index < OOS_END)
    p1_is = p1[is_mask]
    p2_is = p2[is_mask]
    p1_oos = p1[oos_mask]
    p2_oos = p2[oos_mask]
    
    if len(p1_is) < ZSCORE_WINDOW * 2 or len(p1_oos) < 10:
        return None
    
    f1 = load_funding(s1)
    f2 = load_funding(s2)
    regime_df = load_spread_regime(pair_name)
    
    p1_is_log = np.log(p1_is)
    p2_is_log = np.log(p2_is)
    p1_oos_log = np.log(p1_oos)
    p2_oos_log = np.log(p2_oos)
    
#-----------------------------------------------------------------------------------------------------------
# Some functions and logics are excluded due to copyright issues.
#-----------------------------------------------------------------------------------------------------------


def compute_portfolio_metrics(all_trades, initial_capital, n_pairs):
    """Portfolio 성과."""
    if not all_trades:
        return None
    
    df = pd.DataFrame(all_trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    
    capital_per_pair = initial_capital / n_pairs
    df['pnl'] = capital_per_pair * df['net_return']
    df = df.sort_values('exit_time').reset_index(drop=True)
    
    n_trades = len(df)
    total_pnl = df['pnl'].sum()
    total_return = total_pnl / initial_capital
    win_rate = (df['net_return'] > 0).mean()
    
    df['equity'] = initial_capital + df['pnl'].cumsum()
    running_max = df['equity'].cummax()
    dd = (df['equity'] - running_max) / running_max
    mdd = dd.min() * 100
    
    period_days = (df['entry_time'].max() - df['entry_time'].min()).days
    n_years = max(period_days / 365, 0.1)
    trades_per_year = n_trades / n_years
    mean_r = df['net_return'].mean()
    std_r = df['net_return'].std()
    sharpe = (mean_r / (std_r + 1e-9)) * np.sqrt(trades_per_year)
    
    return {
        'n_trades': n_trades,
        'total_return_pct': total_return * 100,
        'sharpe': sharpe,
        'mdd_pct': mdd,
        'win_rate_pct': win_rate * 100,
    }

#-----------------------------------------------------------------------------------------------------------
  
def run_iteration(iter_num, all_pair_results, all_pairs, pair_fraction, capital):
    """한 iteration: 랜덤 pair subset으로 성과 계산."""
    np.random.seed(iter_num)
    n_select = int(len(all_pairs) * pair_fraction)
    selected_idx = np.random.choice(len(all_pairs), n_select, replace=False)
    selected_pairs = [all_pairs[i] for i in selected_idx]
    
    # 선택된 pair의 trades 수집
    trades = []
    valid_pair_count = 0
    for pair_name in selected_pairs:
        r = all_pair_results.get(pair_name)
        if r and r['trades']:
            trades.extend(r['trades'])
            valid_pair_count += 1
    
    if not trades:
        return None
    
    metrics = compute_portfolio_metrics(trades, capital, valid_pair_count)
    if metrics is None:
        return None
    metrics['iteration'] = iter_num
    metrics['n_pairs_selected'] = valid_pair_count
    return metrics

#-----------------------------------------------------------------------------------------------------------
  
def main():
    print("=" * 70)
    print(f" Bootstrap Pair Robustness Test")
    print(f" Iterations: {N_ITERATIONS}, Pair fraction: {PAIR_FRACTION*100:.0f}%")
    print("=" * 70)
    
    # 전체 pair backtest 한 번만 (재사용)
    pairs_df = pd.read_parquet(DATA_DIR / f"perp_tradeable_{TF}.parquet")
    print(f"\n Total pairs: {len(pairs_df)}")
    
    print(f"\n Backtesting all pairs (one-time)...")
    pair_dicts = pairs_df.to_dict('records')
    results = Parallel(n_jobs=-1, verbose=5)(
        delayed(backtest_pair)(p) for p in pair_dicts
    )
    
    # Dict으로 변환
    all_pair_results = {r['pair']: r for r in results if r is not None}
    all_pairs = list(all_pair_results.keys())
    print(f"Valid pairs: {len(all_pairs)}")
    
    # Baseline (전체 pair) 성과
    all_trades = []
    for r in all_pair_results.values():
        all_trades.extend(r['trades'])
    baseline = compute_portfolio_metrics(all_trades, INITIAL_CAPITAL, len(all_pairs))
    print(f"\n=== Baseline (All {len(all_pairs)} pairs) ===")
    print(f"Sharpe: {baseline['sharpe']:.2f}")
    print(f"Return: {baseline['total_return_pct']:.2f}%")
    print(f"MDD: {baseline['mdd_pct']:.2f}%")
    print(f"Win rate: {baseline['win_rate_pct']:.1f}%")
    
    # Bootstrap iterations
    print(f"\n=== Bootstrap {N_ITERATIONS} iterations ===")
    iter_results = []
    for i in tqdm(range(N_ITERATIONS)):
        m = run_iteration(i, all_pair_results, all_pairs, PAIR_FRACTION, INITIAL_CAPITAL)
        if m:
            iter_results.append(m)
    
    if not iter_results:
        print("No valid iterations.")
        return
    
    # Distribution 분석
    df = pd.DataFrame(iter_results)
    print(f"\n{'#'*70}")
    print(f"# Distribution Analysis")
    print(f"{'#'*70}")
    
    for metric in ['sharpe', 'total_return_pct', 'mdd_pct', 'win_rate_pct']:
        vals = df[metric]
        print(f"\n{metric}:")
        print(f"  Mean:   {vals.mean():+.2f}")
        print(f"  Median: {vals.median():+.2f}")
        print(f"  Std:    {vals.std():.2f}")
        print(f"  Min:    {vals.min():+.2f}")
        print(f"  Max:    {vals.max():+.2f}")
        print(f"  5% pct: {vals.quantile(0.05):+.2f}")
        print(f"  25% pct: {vals.quantile(0.25):+.2f}")
        print(f"  75% pct: {vals.quantile(0.75):+.2f}")
        print(f"  95% pct: {vals.quantile(0.95):+.2f}")
    
    # 판정
    print(f"\n{'#'*70}")
    print(f"# 판정")
    print(f"{'#'*70}")
    sharpe_5 = df['sharpe'].quantile(0.05)
    positive_ratio = (df['sharpe'] > 0).mean() * 100
    print(f"Sharpe 5% percentile: {sharpe_5:.2f}")
    print(f"Positive Sharpe ratio: {positive_ratio:.1f}%")
    
    if sharpe_5 > 0.5:
        print("→ ROBUST (5% percentile > 0.5)")
    elif sharpe_5 > 0:
        print("→ ACCEPTABLE (5% percentile > 0, marginal)")
    else:
        print("→ FRAGILE (5% percentile <= 0)")

if __name__ == "__main__":
    main()
