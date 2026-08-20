"""
Phase 2: Cointegration test.

Input: pair_correlations.parquet (50 pairs).
Test: Engle-Granger + Johansen + Residual ADF.

"""
import sys
sys.path.append('My_Local_Path')

import pandas as pd
import numpy as np
from pathlib import Path
from tqdm import tqdm
from statsmodels.tsa.stattools import coint, adfuller
from statsmodels.tsa.vector_ar.vecm import coint_johansen
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant
import warnings
warnings.filterwarnings('ignore')

DATA_DIR = Path("My_Local_Path")

#------------------------------------------------------------------------------------
# Parameters are excluded due to copyright issue. 
EG_P_THRESHOLD = n1
ADF_P_THRESHOLD = n2
TIMEFRAME = '1h'
MIN_BARS = n3
#------------------------------------------------------------------------------------


def load_price(symbol):
    """자산의 spot close."""
    path = DATA_DIR / f"spot_{symbol}_{TIMEFRAME}.parquet"
    df = pd.read_parquet(path)
    if 'open_time' in df.columns:
        df = df.set_index('open_time')
    df.index = pd.to_datetime(df.index, utc=True)
    return df['close']


def test_cointegration(s1, s2):
    """
    Cointegration test for both two assets, used by tools:
        - Engle-Granger.
        - Johansen (trace stat vs 95% critical).
        - Residual ADF (OLS residual).
    """
    p1 = load_price(s1)
    p2 = load_price(s2)
    
    common = p1.dropna().index.intersection(p2.dropna().index)
    if len(common) < MIN_BARS:
        return None
    
    p1_c = np.log(p1.loc[common])
    p2_c = np.log(p2.loc[common])
    
    result = {
        'symbol_1': s1,
        'symbol_2': s2,
        'n_bars': len(common),
        'start_time': common[0],
        'end_time': common[-1],
    }
    
    # 1. Engle-Granger
    try:
        eg_stat, eg_p, _ = coint(p1_c, p2_c)
        result['eg_stat'] = eg_stat
        result['eg_p'] = eg_p
    except Exception:
        result['eg_stat'] = np.nan
        result['eg_p'] = np.nan
    
    # 2. Johansen
    try:
        pair_df = pd.concat([p1_c, p2_c], axis=1)
        johansen = coint_johansen(pair_df, det_order=0, k_ar_diff=1)
        trace_stat = johansen.lr1[0]
        crit_95 = johansen.cvt[0, 1]
        result['johansen_trace'] = trace_stat
        result['johansen_crit_95'] = crit_95
        result['johansen_significant'] = trace_stat > crit_95
    except Exception:
        result['johansen_trace'] = np.nan
        result['johansen_crit_95'] = np.nan
        result['johansen_significant'] = False
    
    # 3. OLS hedge ratio + residual ADF
    try:
        X = add_constant(p2_c)
        model = OLS(p1_c, X).fit()
        result['hedge_ratio'] = model.params.iloc[1]
        result['intercept'] = model.params.iloc[0]
        
        residuals = p1_c - result['hedge_ratio'] * p2_c - result['intercept']
        adf_result = adfuller(residuals.dropna(), autolag='AIC')
        result['residual_adf_stat'] = adf_result[0]
        result['residual_adf_p'] = adf_result[1]
        
        # Half-life 계산 (OU process fit)
        spread_lag = residuals.shift(1).dropna()
        spread_diff = residuals.diff().dropna()
        spread_lag = spread_lag.loc[spread_diff.index]
        
        X_hl = add_constant(spread_lag)
        hl_model = OLS(spread_diff, X_hl).fit()
        b = hl_model.params.iloc[1]
        
        if b < 0:
            half_life_bars = -np.log(2) / b
            result['half_life_hours'] = half_life_bars  # 1h bars
            result['half_life_days'] = half_life_bars / 24
        else:
            result['half_life_hours'] = np.nan
            result['half_life_days'] = np.nan
        
    except Exception:
        result['hedge_ratio'] = np.nan
        result['intercept'] = np.nan
        result['residual_adf_stat'] = np.nan
        result['residual_adf_p'] = np.nan
        result['half_life_hours'] = np.nan
        result['half_life_days'] = np.nan
    
    return result


def main():
    print("=" * 70)
    print("Phase 2: 1H Cointegration Test")
    print("=" * 70)
    
    corr_df = pd.read_parquet(DATA_DIR / "pair_correlations.parquet")
    print(f"Input pairs (from correlation): {len(corr_df):,}")
    print(f"Testing: EG + Johansen + Residual ADF")
    print(f"Threshold: EG p < {EG_P_THRESHOLD}, Johansen 95%, ADF p < {ADF_P_THRESHOLD}")
    
    results = []
    for _, row in tqdm(corr_df.iterrows(), total=len(corr_df),
                       desc="Cointegration"):
        res = test_cointegration(row['symbol_1'], row['symbol_2'])
        if res is not None:
            res['correlation'] = row['correlation']
            results.append(res)
    
    results_df = pd.DataFrame(results)
    
    if len(results_df) == 0:
        print("No results.")
        return
    
    # 각 test 통과 개수
    eg_passed = results_df['eg_p'] < EG_P_THRESHOLD
    johansen_passed = results_df['johansen_significant']
    adf_passed = results_df['residual_adf_p'] < ADF_P_THRESHOLD
    
    all_passed = eg_passed & johansen_passed & adf_passed
    passed = results_df[all_passed].sort_values('eg_p').reset_index(drop=True)
    
    print(f"\n=== Cointegration Results ===")
    print(f"Total tested: {len(results_df):,}")
    print(f"  EG passed (p < {EG_P_THRESHOLD}): {eg_passed.sum():,}")
    print(f"  Johansen passed: {johansen_passed.sum():,}")
    print(f"  Residual ADF passed (p < {ADF_P_THRESHOLD}): {adf_passed.sum():,}")
    print(f"  ALL 3 passed: {all_passed.sum():,}")
    
    if len(passed) > 0:
        print(f"\n=== Final passed pairs ({len(passed)}) ===")
        display_cols = ['symbol_1', 'symbol_2', 'correlation', 'eg_p',
                       'residual_adf_p', 'hedge_ratio', 'half_life_days']
        print(passed[display_cols].to_string())
        
        # Half-life 분포
        hl_valid = passed['half_life_days'].dropna()
        if len(hl_valid) > 0:
            print(f"\n=== Half-life 분포 (days) ===")
            print(f"  Min: {hl_valid.min():.2f}")
            print(f"  Max: {hl_valid.max():.2f}")
            print(f"  Median: {hl_valid.median():.2f}")
            print(f"  < 7 days: {(hl_valid < 7).sum()}")
            print(f"  < 30 days: {(hl_valid < 30).sum()}")
    
    # Save
    results_df.to_parquet(DATA_DIR / "pair_cointegration_all.parquet",
                         engine='pyarrow', compression='snappy')
    passed.to_parquet(DATA_DIR / "pair_final_passed.parquet",
                     engine='pyarrow', compression='snappy',

if __name__ == "__main__":
    main()
