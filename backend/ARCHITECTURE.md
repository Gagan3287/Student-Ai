# StudyMate AI — Architecture Notes

## Phase 6: Memory Retention Model

### Overview

The retention predictor estimates the probability that a student still remembers a flashcard at the time of scheduling a review. This probability is stored as `retention_probability` on the `Flashcard` row and is updated after every review submission.

**Pipeline:**
```
Student reviews a flashcard
        ↓
SM-2 algorithm updates interval, repetitions, and easiness (sm2.py)
        ↓
RetentionPredictor.predict(features) called with 6 review-history features
        ↓
GBR.predict(X) → expm1() → max(0.1, h) → P = 2^(-t/h) ∈ [0, 1]
        ↓
retention_probability stored to DB
```

**Inference file:** `backend/app/ml/retention_inference.py`  
**Training notebook:** `backend/ml/train_retention_model.ipynb`  
**Exported model:** `backend/ml/retention_model.joblib`

---

### Synthetic Data Bootstrap

Real longitudinal review data (weeks/months of actual user sessions) does not exist at deployment time. Following the same bootstrapping approach used by Duolingo's Half-Life Regression research, we generate 5,000 synthetic review sessions whose target half-life values are derived analytically from cognitive-science first principles:

- **Base half-life:** Scaled inversely by `question_difficulty` (harder cards decay faster)
- **Expansion factor:** `1.5^correct_count × 0.6^incorrect_count` — successful retrievals compound memory strength exponentially; failures compound decay
- **Hesitation penalty:** `0.9^max(0, avg_response_time_s − 2)` — slow responses indicate weaker encoding
- **Spacing multiplier:** `1 + 0.05 × days_since_last_review × accuracy` — desirable difficulty: retrievals after longer gaps strengthen the trace more
- **Log-normal noise:** `σ = 0.15` — models natural inter-subject variability in memory consolidation

As real user reviews accumulate, the model can be periodically retrained on actual data to replace this bootstrap.

---

### Features

| # | Feature | Type | Cognitive rationale |
|---|---|---|---|
| 1 | `review_count` | int | Total exposures strengthen the memory trace |
| 2 | `correct_count` | int | Active successful retrievals expand half-life |
| 3 | `incorrect_count` | int | Failures reset / weaken the memory trace |
| 4 | `avg_response_time_s` | float | Hesitation is a proxy for weak encoding |
| 5 | `days_since_last_review` | float | Spacing effect: longer gaps before recall strengthen trace |
| 6 | `question_difficulty` | float | Inverse SM-2 easiness — harder cards decay faster |

---

### Model Iteration Log

The model went through two training iterations during development.

#### v1 — Raw Target (GBR on `half_life`)

The first version trained the GradientBoostingRegressor directly on raw half-life values (0.1–365 days). The target distribution is highly right-skewed (median ≈ 1.8 days, std ≈ 101 days, p95 ≈ 353 days). Because GBR minimises MSE, the tail dominated training — large-h errors were penalised disproportionately, pulling the model away from accurate predictions for the majority of cards (67% of cards have h ≤ 7 days).

| Split | MAE | RMSE |
|---|---|---|
| Held-out test (80/20, 1,000 samples) | **7.1749 days** | **16.6582 days** |

#### v2 — Log-Transform (GBR on `log1p(half_life)`) ← current

Transforming the target with `log1p` compresses the tail so the model learns relative error uniformly across the full range. At inference, `expm1()` inverts the prediction back to days. The `max(0.1, h)` floor is retained to guard against any near-zero expm1 outputs on extrapolated inputs.

| Split | MAE | RMSE |
|---|---|---|
| Held-out test (80/20, 1,000 samples) | **6.8071 days** | **19.5937 days** |

**Interpretation:** MAE improved by 0.37 days (~5%) because predictions for short-half-life cards (h ≤ 7d, representing 67% of the dataset) became substantially more accurate — per-range evaluation shows MAE of just **0.24 days** for this bucket. The RMSE increase (+2.9 days) reflects the fact that `expm1` amplifies log-space errors back onto the extreme long-lived cards (h > 30d, 21% of samples), where errors remain large (MAE ~30 days) because the model correctly deprioritises the tail in log-space. Since long-lived cards are already well-retained and their exact half-life has minimal practical impact on scheduling, this is an acceptable trade-off.

> **For the final report:** The evaluation split used throughout is an 80/20 train-test split (`random_state=42`). All metrics are computed on the held-out 1,000-sample test set. The model was never evaluated on its own training data.

---

### Inference Behaviour

**When `retention_model.joblib` is present (normal production path):**
```python
log_h   = GBR.predict([[review_count, correct_count, ...]])[0]
h       = max(0.1, math.expm1(log_h))   # invert log-transform + floor
P       = 2 ** (-t / h)                  # Duolingo HLR formula
```

**When joblib is missing (fresh clone, fallback path):**
```python
# Heuristic using SM-2 easiness + Ebbinghaus curve
strength = (1 - difficulty) * (0.5 + 0.5*accuracy) * (1 + 0.2*review_count)
P = exp(-t / max(0.5, strength * 10))
```
