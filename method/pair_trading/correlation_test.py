"""
Phase 1: Correlation sweep.

대상: 1년 + 데이터 있는 자산.
Timeframe: 1h (sub-sample).
Threshold: Excluded due to copyright issue.
Min overlap: also excluded due to copyright issue. 

Output: pair_correlations.parquet
"""
import sys
sys.path.append('My_Path')  # 주소 공유 불가.

import pandas as pd
import numpy as np
from pathlib import Path
from itertools import combinations
from tqdm import tqdm
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("My_Local_Path")  # 주소 공유 불가.

""" # Methodology Paramters are excluded due to copyright issue. 
CORR_THRESHOLD = n1
MIN_OVERLAP_DAYS = n2
MIN_DATA_DAYS = n3
TIMEFRAME = '1h'
"""

def load_qualifying_symbols():
  
    report = pd.read_csv(DATA_DIR / "sanity_report.csv")
    
    qualifying = report[
        (report['spot_1h_exists']) &
        (report['futures_um_1h_exists']) &
        (report['spot_1h_days'] >= MIN_DATA_DAYS)
    ]['base'].tolist()
    
    return qualifying


def load_all_prices(symbols):
    """자격 자산의 spot close 로드."""
    print(f"Loading {len(symbols)} symbols...")
    prices = {}
    
    for base in tqdm(symbols, desc="Loading"):
        symbol = f"{base}USDT"
        path = DATA_DIR / f"spot_{symbol}_{TIMEFRAME}.parquet"
        
        if not path.exists():
            continue
        
        try:
            df = pd.read_parquet(path)
            if 'open_time' in df.columns:
                df = df.set_index('open_time')
            df.index = pd.to_datetime(df.index, utc=True)
            
            if 'close' in df.columns:
                prices[symbol] = df['close']
        except Exception:
            continue
    
    result = pd.DataFrame(prices).sort_index()
    print(f"Loaded: {len(result.columns)} symbols, {len(result):,} timestamps")
    return result


def compute_correlations(prices):
    """Pair-wise log returns correlation."""
    print("\nComputing log returns...")
    log_returns = np.log(prices).diff().dropna(how='all')
    
    symbols = list(log_returns.columns)
    n = len(symbols)
    total_pairs = n * (n - 1) // 2
    print(f"Symbols: {n}, Total pairs: {total_pairs:,}")
    
    results = []
    min_overlap_bars = MIN_OVERLAP_DAYS * 24
    
    for i, j in tqdm(list(combinations(range(n), 2)), desc="Correlations"):
        s1, s2 = symbols[i], symbols[j]
        
        r1 = log_returns[s1]
        r2 = log_returns[s2]
        
        # Overlap
        common = r1.dropna().index.intersection(r2.dropna().index)
        if len(common) < min_overlap_bars:
            continue
        
        r1_c = r1.loc[common]
        r2_c = r2.loc[common]
        
        try:
            corr = r1_c.corr(r2_c)
        except:
            continue
        
        if pd.isna(corr):
            continue
        
        if abs(corr) >= CORR_THRESHOLD:
            results.append({
                'symbol_1': s1,
                'symbol_2': s2,
                'correlation': corr,
                'n_overlap_bars': len(common),
                'start_time': common[0],
                'end_time': common[-1],
            })
    
    return pd.DataFrame(results)


def main():
    print("=" * 70)
    print(f"Phase 1: Correlation Sweep")
    print(f"|r| >= {CORR_THRESHOLD}, Min data {MIN_DATA_DAYS} days, "
          f"Min overlap {MIN_OVERLAP_DAYS} days")
    print("=" * 70)
    
    symbols = load_qualifying_symbols()
    print(f"Qualifying symbols: {len(symbols)}")
    
    prices = load_all_prices(symbols)
    
    if len(prices.columns) < 2:
        print("Not enough symbols.")
        return
    
    results = compute_correlations(prices)
    
    if len(results) == 0:
        print("No pairs passed.")
        return
    
    results['abs_corr'] = results['correlation'].abs()
    results = results.sort_values('abs_corr', ascending=False).reset_index(drop=True)
    
    print(f"\n=== Results ===")
    print(f"Pairs passing |r| >= {CORR_THRESHOLD}: {len(results):,}")
    
    print(f"\n=== Correlation 분포 ===")
    for th in [0.6, 0.7, 0.8, 0.9]:
        n = (results['abs_corr'] >= th).sum()
        print(f"  |r| >= {th}: {n:,}")
    
    out_path = DATA_DIR / "pair_correlations.parquet"
    results.to_parquet(out_path, engine='pyarrow', compression='snappy')
    print(f"\nSaved: {out_path}")


if __name__ == "__main__":
    main()
