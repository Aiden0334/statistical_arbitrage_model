"""
< Parameter Sensitivity Test >

* 목적:
    파라미터 ±20% 변화 시 성능 안정성 확인.
    급락 파라미터가 있으면 fragile.

* Baseline (parameters are excluded due to copyright issue)

* 판정:
    - Sharpe 편차 < 0.3: 안정.
    - Sharpe 편차 > 0.5: 민감 (파라미터 튜닝 위험).
"""
import sys
sys.path.append('My_Local_Path2')

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from joblib import Parallel, delayed
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("My_Local_Data_Set2")
REGIME_DIR = DATA_DIR / "regimes2"


#-----------------------------------------------------------------------------------------
# Parameters are excluded due to copyright issue. 
#-----------------------------------------------------------------------------------------


IS_START = pd.Timestamp('2020-01-01', tz='UTC')
IS_END = pd.Timestamp('2026-01-01', tz='UTC')
OOS_START = pd.Timestamp('2026-01-01', tz='UTC')
OOS_END = pd.Timestamp('2026-08-01', tz='UTC')


def load_price(symbol):
    # excluded.


def load_funding(symbol):
    # excluded.


def load_spread_regime(pair_name):
    # excluded. 


def ols_hedge(p1_log, p2_log):
    X = add_constant(p2_log)
    model = OLS(p1_log, X).fit()
    return model.params.iloc[1], model.params.iloc[0]


def compute_funding_pnl(f1, f2, entry_time, exit_time, direction, hedge_ratio):
    # excluded.


def get_spread_allow(timestamp, regime_df):
    if regime_df is None:
        return True
    try:
        row = regime_df.loc[regime_df.index <= timestamp].iloc[-1]
        return row['trade_allowed']
    except (IndexError, KeyError):
        return True


def backtest_pair(pair_row, z_entry, z_exit, zscore_window):
    # excluded.
    
    common = p1.dropna().index.intersection(p2.dropna().index)
    p1 = p1.loc[common]
    p2 = p2.loc[common]
    
    is_mask = (p1.index >= IS_START) & (p1.index < IS_END)
    oos_mask = (p1.index >= OOS_START) & (p1.index < OOS_END)
    p1_is = p1[is_mask]
    p2_is = p2[is_mask]
    p1_oos = p1[oos_mask]
    p2_oos = p2[oos_mask]
    
    # excluded.
    
    hedge_series = pd.Series(hedge_ratio, index=p1_oos.index)
    zscore_oos = (spread_oos - mean_is) / std_is
    
    trades = []
    in_position = False
    entry_idx = None
    entry_z = None
    entry_p1 = None
    entry_p2 = None
    entry_hedge = None
    entry_time = None
    direction = 0
    
    z_vals = zscore_oos.values
    p1_vals = p1_oos.values
    p2_vals = p2_oos.values
    h_vals = hedge_series.values
    idx = zscore_oos.index
    
    for i in range(len(z_vals)):
        z = z_vals[i]
        if pd.isna(z):
            continue
        current_time = idx[i]
        allow = get_spread_allow(current_time, regime_df)
        
        if not in_position:
            if not allow:
                continue
            if abs(z) > z_entry:
                in_position = True
                entry_idx = i
                entry_z = z
                entry_p1 = p1_vals[i]
                entry_p2 = p2_vals[i]
                entry_hedge = h_vals[i]
                entry_time = current_time
                direction = -1 if z > 0 else 1
        else:
            duration = i - entry_idx
            current_p1 = p1_vals[i]
            current_p2 = p2_vals[i]
            
            # entry/exit logic excluded.
            
            if exit_reason:
                # features excluded.
    
    return {'pair': pair_name, 'trades': trades}


def run_config(z_entry, z_exit, zscore_window):
    pairs_df = pd.read_parquet(DATA_DIR / f"perp_tradeable_{TF}.parquet")
    pair_dicts = pairs_df.to_dict('records')
    
    results = Parallel(n_jobs=-1, verbose=0)(
        delayed(backtest_pair)(parameters characteristics)
        for p in pair_dicts
    )
    
    valid = [r for r in results if r and r['trades']]
    if not valid:
        return None
    
    n_pairs = len(valid)
    capital_per_pair = INITIAL_CAPITAL / n_pairs
    
    all_trades = []
    for r in valid:
        for t in r['trades']:
            t['pnl'] = capital_per_pair * t['net_return']
            all_trades.append(t)
    
    df = pd.DataFrame(all_trades)
    df['entry_time'] = pd.to_datetime(df['entry_time'])
    df['exit_time'] = pd.to_datetime(df['exit_time'])
    df = df.sort_values('exit_time').reset_index(drop=True)
    
    n_trades = len(df)
    total_pnl = df['pnl'].sum()
    total_return = total_pnl / INITIAL_CAPITAL
    win_rate = (df['net_return'] > 0).mean()
    
    df['equity'] = INITIAL_CAPITAL + df['pnl'].cumsum()
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
        'z_entry': z_entry,
        'z_exit': z_exit,
        'zscore_window': zscore_window,
        'n_trades': n_trades,
        'total_return_pct': total_return * 100,
        'sharpe': sharpe,
        'mdd_pct': mdd,
        'win_rate_pct': win_rate * 100,
    }


def main():
    print("=" * 70)
    print(f"Parameter Sensitivity Test")
    print(f"Baseline: Z_ENTRY=2.0, Z_EXIT=0.5, ZSCORE_WINDOW=30")
    print("=" * 70)
    
    results = []
    
    # Z_ENTRY sweep
    print(f"\n=== Z_ENTRY sweep (baseline z_exit=0.5, window=30) ===")
    for z_entry in tqdm([n1, n2, n3, n4, n5], desc="Z_ENTRY"):
        r = run_config(z_entry, p-value, n_days)
        if r:
            r['param'] = 'Z_ENTRY'
            r['value'] = z_entry
            results.append(r)
            print(f"  Z_ENTRY={z_entry}: Sharpe={r['sharpe']:.2f}, "
                  f"Return={r['total_return_pct']:+.2f}%, MDD={r['mdd_pct']:.2f}%, "
                  f"Trades={r['n_trades']}")
    
    # Z_EXIT sweep
    print(f"\n=== Z_EXIT sweep (baseline z_entry=2.0, window=30) ===")
    for z_exit in tqdm([n1, n2, n3, n4, n5], desc="Z_EXIT"):
        r = run_config(n_threshold2, z_exit, n_days)
        if r:
            r['param'] = 'Z_EXIT'
            r['value'] = z_exit
            results.append(r)
            print(f"  Z_EXIT={z_exit}: Sharpe={r['sharpe']:.2f}, "
                  f"Return={r['total_return_pct']:+.2f}%, MDD={r['mdd_pct']:.2f}%, "
                  f"Trades={r['n_trades']}")
    
    # ZSCORE_WINDOW sweep
    print(f"\n=== ZSCORE_WINDOW sweep (baseline z_entry=2.0, z_exit=0.5) ===")
    # logics are excluded.
    
    # 판정
    print(f"\n{'#'*70}")
    print(f"# Sensitivity Analysis")
    print(f"{'#'*70}")
    
    df = pd.DataFrame(results)
    for param in ['Z_ENTRY', 'Z_EXIT', 'ZSCORE_WINDOW']:
        sub = df[df['param'] == param]
        sharpe_range = sub['sharpe'].max() - sub['sharpe'].min()
        sharpe_std = sub['sharpe'].std()
        print(f"\n{param}:")
        print(f"  Sharpe range: {sub['sharpe'].min():.2f} ~ {sub['sharpe'].max():.2f}")
        print(f"  Sharpe std: {sharpe_std:.2f}")
        if sharpe_range < 0.3:
            print(f"  → STABLE")
        elif sharpe_range < 0.5:
            print(f"  → MODERATE")
        else:
            print(f"  → SENSITIVE (파라미터 민감)")


if __name__ == "__main__":
    main()
