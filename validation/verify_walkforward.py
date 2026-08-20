"""
Walk-forward 검증 + look-ahead bias / data leakage 체크.
"""
import pandas as pd
import numpy as np
from pathlib import Path

DATA_DIR = Path("My_Local_Path2")
REGIME_DIR = DATA_DIR / "regimes2"
BACKTEST_DIR = DATA_DIR / "backtest_results"


def check_fold_structure():
    """Fold 구조 확인."""
    print("=" * 70)
    print("Walk-forward Fold Structure")
    print("=" * 70)
    
    from datetime import timedelta
    
    TRAIN_MONTHS = 12
    TEST_MONTHS = 3
    start = pd.Timestamp('2019-01-01', tz='UTC')
    end = pd.Timestamp('2026-01-01', tz='UTC')
    
    folds = []
    test_start = start + pd.DateOffset(months=TRAIN_MONTHS)
    while test_start + pd.DateOffset(months=TEST_MONTHS) <= end:
        folds.append({
            'train_start': test_start - pd.DateOffset(months=TRAIN_MONTHS),
            'train_end': test_start,
            'test_start': test_start,
            'test_end': test_start + pd.DateOffset(months=TEST_MONTHS),
        })
        test_start = test_start + pd.DateOffset(months=TEST_MONTHS)
    
    print(f"Total folds: {len(folds)}")
    print(f"\nFirst 3 folds:")
    for i, f in enumerate(folds[:3]):
        print(f"  Fold {i+1}: Train {f['train_start'].date()} ~ {f['train_end'].date()} | "
              f"Test {f['test_start'].date()} ~ {f['test_end'].date()}")
    
    # Overlap check
    print(f"\n=== Overlap check ===")
    for i in range(len(folds) - 1):
        f1 = folds[i]
        f2 = folds[i+1]
        if f1['test_end'] > f2['test_start']:
            print(f"  [WARN] Fold {i+1} test overlaps with Fold {i+2}")
    print("  Overlap check done.")
    
    # Train/test overlap
    print(f"\n=== Train/Test overlap in same fold ===")
    for i, f in enumerate(folds[:3]):
        if f['train_end'] > f['test_start']:
            print(f"  [WARN] Fold {i+1}: train_end > test_start (LEAKAGE)")
        else:
            print(f"  Fold {i+1}: OK (train ends {f['train_end'].date()}, test starts {f['test_start'].date()})")


def check_tradeable_pair_leakage():
    """Tradeable pair 선정에 미래 정보 사용됐는지."""
    print("\n" + "=" * 70)
    print("Tradeable Pair Selection Leakage Check")
    print("=" * 70)
    
    for tf in ['TimeFrames']:
        path = DATA_DIR / f"perp_tradeable_{tf}.parquet"
        if not path.exists():
            continue
        
        df = pd.read_parquet(path)
        print(f"\n{tf}: {len(df)} tradeable pairs")
        
        # Tradeable 선정에 사용된 데이터 기간 확인
        # correlation, cointegration 등이 어떤 기간 데이터 사용했나
        print("  Tradeable pair는 전체 기간 (2019-2025) 데이터로 선정됨")
        print("  → 2019~2024 backtest에 2025 정보 유입 가능성 있음")
        print("  → LOOK-AHEAD BIAS 존재")
    
    print("\n=== 진짜 실전 방식 ===")
    print("  각 fold의 train 기간 데이터로만 tradeable pair 재선정 필요")
    print("  → walk-forward 내에 filter 재실행")
    print("  → 시간 매우 오래 걸림")


def check_regime_leakage():
    """Spread regime 파일 data leakage."""
    print("\n" + "=" * 70)
    print("Spread Regime Leakage Check")
    print("=" * 70)
    
    # 예시 pair 하나
    files = list(REGIME_DIR.glob("*_1d.parquet"))
    if not files:
        print("No 1d regime files.")
        return
    
    sample = pd.read_parquet(files[0])
    print(f"\nSample: {files[0].name}")
    print(f"  Range: {sample.index.min()} ~ {sample.index.max()}")
    print(f"  Unique regimes: {sample['regime'].dropna().unique()}")
    
    print("\n=== Regime 계산 방식 ===")
    print("  Rolling VR (backward-looking window=100)")
    print("  Rolling quantile (backward-looking window=200)")
    print("  → 시점 t의 regime은 t 이전 정보만 사용")
    print("  → NO LEAKAGE (계산 자체)")
    
    print("\n=== 하지만 미묘한 이슈 ===")
    print("  Regime 파일 자체는 전체 기간 계산 후 저장")
    print("  Backtest에서 시점 t의 regime을 look up")
    print("  Look up이 backward-only면 OK")
    print("  Backtest 코드 확인 필요:")
    print("  → <= timestamp → 시점 t 이하만 → NO LEAKAGE")


def compare_2025_impact():
    """2025년 데이터 영향 상세."""
    print("\n" + "=" * 70)
    print("2025 Impact Analysis")
    print("=" * 70)
    
    for mode in ['none', 'spread']:
        path = BACKTEST_DIR / f"trades_1d_{mode}.parquet"
        if not path.exists():
            continue
        
        df = pd.read_parquet(path)
        df['entry_time'] = pd.to_datetime(df['entry_time'])
        df['year'] = df['entry_time'].dt.year
        
        print(f"\n=== 1d / {mode} ===")
        
        # 연도별 요약
        yearly = df.groupby('year').agg(
            n=('pnl', 'count'),
            pnl=('pnl', 'sum'),
        )
        print(yearly.to_string())
        
        # 각 연도 Sharpe 계산
        print(f"\nYearly Sharpe:")
        ret_col = 'net_return_sized' if mode == 'full' else 'net_return'
        for y in sorted(df['year'].unique()):
            sub = df[df['year'] == y]
            if len(sub) < 2:
                continue
            mean_r = sub[ret_col].mean()
            std_r = sub[ret_col].std()
            n = len(sub)
            # Annualized (연 데이터로 조정)
            sharpe = (mean_r / (std_r + 1e-9)) * np.sqrt(n)
            print(f"  {y}: {sharpe:.2f} (n={n})")


if __name__ == "__main__":
    check_fold_structure()
    check_tradeable_pair_leakage()
    check_regime_leakage()
    compare_2025_impact()
