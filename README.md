# Regime-Aware Statistical Arbitrage in Crypto Perpetual Futures

> Variance Ratio 기반 regime classifier를 크립토 pair trading에 적용한 개인 quant 프로젝트.

**Status**: Out-of-sample forward test 검증 완료 → Paper trading 배포 진행 중.

---

## Abstract

크립토 Perpetual Futures 시장에서 statistical arbitrage는 개인 quant에게 어려운 영역이다. 본 프로젝트는 5번의 실패 끝에 도달한 하나의 접근법을 기록한다: **spread의 regime 상태를 동적으로 판정해 진입 timing을 필터링하는 pair trading 시스템**.

7개월치 out-of-sample forward test에서 positive risk-adjusted return을 확인했으며, random pair subsampling과 parameter perturbation에도 강건성을 유지했다. 여러 이론적으로 그럴듯한 개선안들이 실증 검증에서 기각되었다.

이 문서는 프로젝트의 **방법론적 여정과 교훈**을 공유한다. 구체적인 구현 세부사항, parameter 값, 알고리즘 상세는 공개하지 않는다.

---

## 1. Motivation

### 왜 크립토 Pair Trading인가?

- Market-neutral (delta-hedged).
- Cointegration이라는 정립된 통계적 근거.
- Perpetual futures로 long/short 모두 가능.
- 24/7 시장.

### 왜 어려운가?

- **Regime shift가 빈번함** — 수개월 유지되던 관계가 몇 주 만에 깨질 수 있음.
- **Cost가 빠르게 누적됨** — Fee + slippage + funding.
- **Alpha가 얇음** — 기관 market maker들이 대부분의 기회를 소멸시킴.

---

## 2. 앞선 시도들

본 프로젝트 이전 5개 접근이 실패:

| # | 접근 | 결과 |
|---|---|---|
| 1 | L1 Statistical Arbitrage | OOS Sharpe 0 근처 |
| 2 | Basis Arbitrage (BTC/ETH) | 모든 조합 OOS negative |
| 3 | Survival Model (Cox + Frailty) | Test C-index coin-flip 수준 |
| 4 | Broad Pair Sweep | Filter pipeline 완성, tradability 증거 없음 |
| 5 | Static Cointegration (오래된 자산) | Stability 통과 pair 0개 |

반복된 실패에서 하나의 질문이 나왔다: **문제가 pair 선정이 아니라 진입 timing이라면?**

---

## 3. 핵심 아이디어

표준 pair trading은 z-score threshold로만 진입한다. 하지만 spread는 시점에 따라 mean-reverting일 수도, trending일 수도 있다.

**Hypothesis**: 현재 spread의 상태 (regime)를 분류할 수 있다면, mean-reverting 상태에서만 진입하는 것이 risk-adjusted return을 개선할 것이다.

---

## 4. 방법론 개요

1. **Universe 선정** — Binance USDT-margined perpetual futures 수백 개 자산.
2. **Pair filter** — 통계적으로 tradeable한 pair 추출 (다단계 filter).
3. **Regime classification** — 각 pair의 spread에 regime classifier 적용.
4. **Backtest** — Walk-forward IS + Pure OOS forward test.
5. **Robustness validation** — Bootstrap, parameter sensitivity.

세부 구현, 파라미터, 알고리즘 상세는 공개하지 않는다.

---

## 5. Journey: 발견과 방향 수정

### Discovery 1: Timeframe이 결정적

초기 예상: 짧은 timeframe = 더 많은 기회 및 샘플 수집 = 더 나은 성능.

**교훈**: 개인 trader에게 cost floor가 timeframe의 hard lower bound를 설정한다. 고빈도 전략은 cost 누적에 파괴된다.

---

### Discovery 2: In-Sample Sharpe는 지나치게 낙관적이었다

Walk-forward backtest가 의심스러울 정도로 높은 Sharpe를 만들어냈다. 조사 결과, 대부분의 이익이 pair가 선정된 최근 기간에 집중되어 있었다. 

---

### Discovery 3: Hold Period는 개선

원래 hold period 상한을 학술 권장 (half-life의 몇 배)에 맞춰 설정했다. 지나치게 관대했다.

<img width="2084" height="741" alt="04_hold_period" src="https://github.com/user-attachments/assets/d3d12cf5-1956-42c5-939c-3ccd06c65965" />


**교훈**: 이론적 parameter는 출발점일 뿐 최종 답이 아니다. 실증 test 필수.

---

### Discovery 4: Regime Filter가 실제로 작동했다

Spread에 regime classifier를 적용했을 때, mean-reversion regime에서만 trading하는 것이 risk-adjusted return을 개선했다.

<img width="1634" height="883" alt="05_mode_comparison" src="https://github.com/user-attachments/assets/15a32163-9222-4d66-ae77-9c200fb35b53" />

Macro overlay 추가는 오히려 성과를 저하 시켰다 — 이미 spread regime과 중복되었기 때문.

---

### Discovery 5: Bootstrap이 강건성 확인

우려: OOS 성능이 소수 pair의 우연 아닌가?

Random pair subsampling (100회 반복, 매번 50%)에서 모든 iteration이 positive Sharpe를 유지했다.

<img width="1484" height="881" alt="02_bootstrap_distribution" src="https://github.com/user-attachments/assets/f9ef08b5-73d7-4469-8ecb-79404680e831" />

**판정**: Alpha는 소수 pair에 집중되지 않고 분산 되어 있다.

---

### Discovery 6: 반직관적인 Cointegration Filter

그럴듯한 개선안: rolling window에서 cointegration을 재확인해 약할 때 진입 skip.

**결과**: Sharpe가 positive에서 강하게 negative로 붕괴.

**진입/청산 기준은 공개하지 않음**

---

### Discovery 7: Portfolio 다각화가 진짜 Hedge

개별 pair 기여도 분석 결과 winner와 loser가 공존했다. 

<img width="1484" height="1781" alt="06_pair_pnl" src="https://github.com/user-attachments/assets/47731594-767b-47a2-80c1-4e75d12c0d75" />

결과: **이것이 pair trading이 작동하는 방식이다**. 각 pair가 이미 delta-neutral hedge이고, 수십 개를 함께 운영하면 statistical diversification이 생성된다. OOS winner에서 선별하려는 시도는 look-ahead bias를 도입해 diversification을 파괴한다.

**판정**: Portfolio를 신뢰하고, winner와 loser를 공존하게 해아 한다. 

---

### Discovery 8: 시도했지만 기각된 것들

여러 이론적으로 그럴듯한 개선안들이 실증 test에서 실패했다.

<img width="1634" height="880" alt="08_rejected_improvements" src="https://github.com/user-attachments/assets/21dab019-7d03-44f0-be27-23995be97447" />

---

## 6. 최종 결과 (Out-of-Sample)

7개월치 held-out forward test: 

Positive Sharpe ratio, drawdown 감내 수준, positive Calmar ratio. Bootstrap 100회 중 최악 시나리오도 positive를 유지.

Parameter sensitivity: entry/exit threshold ±20% 조정에도 Sharpe positive 유지.

---

## 7. Limitations

- **OOS 기간이 7개월뿐**. 통계적 신뢰구간이 넓다.
- **Data universe가 최근 자산으로 편중**. Long-horizon validation 제한.
- **Cost model이 낙관적**. 실전 slippage는 상황에 따라 다름.
- **Regime shift 발생 가능**. 다음 6개월이 tested 기간과 다를 수 있음.
- **Live 성능 미검증**. Paper trading 후 확인 필요.

---

## 8. Deployment Plan

| Stage | 환경 | 성공 기준 |
|---|---|---|
| 1 | Paper trading | Backtest vs live 성능 gap 측정 |
| 2 | Live micro (소액) | Execution mechanics 검증 |
| 3 | Live full | 지속적 performance |
| 4 | Scale | 6개월+ consistent alpha |

각 stage는 hard gate. 실패 시 재검토.

---

## 9. Tech Stack

Python 3.11, Pandas, NumPy, Statsmodels, Joblib, PyArrow. 16-core workstation에서 parallelize.

---

## 10. References

### Pair Trading & Statistical Arbitrage
- Gatev, E., Goetzmann, W. N., & Rouwenhorst, K. G. (2006). "Pairs Trading: Performance of a Relative-Value Arbitrage Rule." *Review of Financial Studies*, 19(3), 797-827.

### Dynamic Hedging
- Elliott, R. J., Van Der Hoek, J., & Malcolm, W. P. (2005). "Pairs Trading." *Quantitative Finance*, 5(3), 271-276.

### Data Source
- Binance Vision — Historical market data. https://data.binance.vision

---

## Disclaimer

교육 및 portfolio 목적. 투자 조언 아님. 과거 performance, 특히 backtest performance는 미래 결과를 보장하지 않는다. Cryptocurrency market은 매우 변동성이 크며 상당한 손실을 초래할 수 있다. 자기 책임 하에 사용.

세부 구현 (algorithm parameter, filter threshold, specific formulas)은 의도적으로 공개하지 않았다. Repository는 방법론적 여정을 공유할 뿐 재현 가능한 실전 시스템을 제공하지 않는다.

---
