"""
Phase 3: Rolling cointegration stability (1h).

Input: pair_final_passed.parquet (1h cointegration 통과).
Test: 6개월 rolling window로 EG cointegration 재계산.
Threshold: n% window에서 EG p < 0.05.

"""
import sys
sys.path.append('My_Local_Path')

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from statsmodels.tsa.stattools import coint
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("My_Local_Data_Set2")

#----------------------------------------------------------------------------------------
# Parameters
WINDOW_MONTHS = 6
STEP_MONTHS = 1
STABILITY_THRESHOLD = n  # n1 to n4 
EG_P_THRESHOLD = 0.05
TIMEFRAME = '1h'
MIN_BARS_PER_WINDOW = 24 * 30 * 3  # 최소 3개월

#----------------------------------------------------------------------------------------

def load_price(symbol):
    """자산의 spot close."""
    path = DATA_DIR / f"spot_{symbol}_{TIMEFRAME}.parquet"
    df = pd.read_parquet(path)
    if 'open_time' in df.columns:
        df = df.set_index('open_time')
    df.index = pd.to_datetime(df.index, utc=True)
    return df['close']

#----------------------------------------------------------------------------------------

def rolling_cointegration(s1, s2, window_bars, step_bars):
    """
    Rolling window로 EG cointegration test.
    각 window의 p-value 반환.
    """
    p1 = load_price(s1)
    p2 = load_price(s2)
    
    common = p1.dropna().index.intersection(p2.dropna().index)
    if len(common) < window_bars * 2:
        return None
    
    p1_c = np.log(p1.loc[common])
    p2_c = np.log(p2.loc[common])
    
    windows = []
    for start_idx in range(0, len(common) - window_bars, step_bars):
        end_idx = start_idx + window_bars
        w1 = p1_c.iloc[start_idx:end_idx]
        w2 = p2_c.iloc[start_idx:end_idx]
        
        if len(w1) < MIN_BARS_PER_WINDOW:
            continue 
        try:
            _, p_val, _ = coint(w1, w2)
            windows.append({
                'window_start': common[start_idx],
                'window_end': common[end_idx - 1],
                'eg_p': p_val,
                'passed': p_val < EG_P_THRESHOLD,
            })
        except Exception:
            continue
    return windows

#----------------------------------------------------------------------------------------

def analyze_stability(windows):
    """
    Rolling windows 결과 요약.
    """
    if not windows or len(windows) == 0:
        return None
    
    df = pd.DataFrame(windows)
    
    n = len(df)
    n_passed = df['passed'].sum()
    passed_fraction = n_passed / n
    
    # Streak analysis (연속 통과)
    consecutive_pass = 0
    max_consecutive = 0
    for passed in df['passed']:
        if passed:
            consecutive_pass += 1
            max_consecutive = max(max_consecutive, consecutive_pass)
        else:
            consecutive_pass = 0
    
    # 최근 3 windows (recent regime)
    recent = df.tail(3)
    recent_passed = recent['passed'].sum() if len(recent) > 0 else 0
    
    return {
        'n_windows': n,
        'n_passed': n_passed,
        'passed_fraction': passed_fraction,
        'max_consecutive_pass': max_consecutive,
        'recent_3_passed': recent_passed,
        'mean_eg_p': df['eg_p'].mean(),
    }

#----------------------------------------------------------------------------------------

def main():
    print("=" * 70)
    print(f"Phase 3: Rolling Cointegration Stability (1h)")
    print("=" * 70)
    print(f"Window: {WINDOW_MONTHS} months")
    print(f"Step: {STEP_MONTHS} month")
    print(f"Stability threshold: {STABILITY_THRESHOLD*100:.0f}% windows passing")
    print(f"EG p threshold per window: {EG_P_THRESHOLD}")
    
    # Input
    passed_df = pd.read_parquet(DATA_DIR / "pair_final_passed.parquet")
    print(f"\n Input pairs (Phase 2 통과): {len(passed_df):,}")
    
    if len(passed_df) == 0:
        print("No pairs to test.")
        return
    
    window_bars = WINDOW_MONTHS * 30 * 24  # months × days × hours
    step_bars = STEP_MONTHS * 30 * 24
    
    results = []
    for _, row in tqdm(passed_df.iterrows(), total=len(passed_df),
                       desc="Rolling"):
        s1, s2 = row['symbol_1'], row['symbol_2']
        
        windows = rolling_cointegration(s1, s2, window_bars, step_bars)
        analysis = analyze_stability(windows)
        
        if analysis is None:
            continue
        
        result = {
            'symbol_1': s1,
            'symbol_2': s2,
            'correlation': row['correlation'],
            'eg_p_full': row['eg_p'],
            'hedge_ratio': row['hedge_ratio'],
            'half_life_days': row.get('half_life_days', np.nan),
        }
        result.update(analysis)
        result['stable'] = analysis['passed_fraction'] >= STABILITY_THRESHOLD
        
        results.append(result)
    
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("No results.")
        return
    
    # 통과 필터링
    stable_df = results_df[results_df['stable']].sort_values(
        'passed_fraction', ascending=False).reset_index(drop=True)
    
    # 결과 출력
    print(f"\n=== Rolling Stability Results (1h) ===")
    print(f"Total tested: {len(results_df):,}")
    print(f"Stable pairs (>= {STABILITY_THRESHOLD*100:.0f}% pass): {len(stable_df):,}")
    
    # Threshold 분포
    print(f"\n=== Passed fraction 분포 ===")
    for th in [n1, n2, n3, n4]:
        n = (results_df['passed_fraction'] >= th).sum()
        print(f"  >= {th*100:.0f}%: {n:,}")

  
    # 최근 windows 통과 (regime 판단)
    # Logic is excluded due to copyright issue.

  
    # Save
    results_df.to_parquet(DATA_DIR / "pair_stability_all.parquet",
                         engine='pyarrow', compression='snappy')
    stable_df.to_parquet(DATA_DIR / "pair_stability_passed.parquet",
                        engine='pyarrow', compression='snappy')
    
    print(f"\nSaved:")
    print(f"  pair_stability_all.parquet (모든 결과)")
    print(f"  pair_stability_passed.parquet (안정적 pair)")


if __name__ == "__main__":
    main()
