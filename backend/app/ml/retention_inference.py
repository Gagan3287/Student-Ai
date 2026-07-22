"""
Retention model inference module — Phase 6 (v2: log-transform GBR).

Loads the scikit-learn GradientBoostingRegressor trained in:
  /backend/ml/train_retention_model.ipynb

The model was trained on log1p(half_life) targets so that it learns
relative error uniformly across the full 0.1–365 day range rather than
being dominated by the extreme right tail. At inference time, we invert
with expm1() before computing the recall probability.

Pipeline:
  features  →  GBR.predict(X)  →  expm1()  →  max(0.1, h)
  →  P(recall) = 2^(-t / h)

At startup: RetentionPredictor.load() is called from main.py's lifespan.
If the joblib file is missing (e.g. fresh clone before running the notebook),
the predictor falls back to a heuristic based on SM-2 easiness.

Memory impact: sklearn + loaded GBR model ≈ 20–25 MB RSS — safe on Render.
"""

import logging
import math
import os
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)

# Path to the exported model, relative to this file's location
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "ml", "retention_model.joblib")
_MODEL_PATH = os.path.normpath(_MODEL_PATH)


@dataclass
class RetentionFeatures:
    """
    Input features for the retention model.
    These map 1-to-1 to the columns trained in the notebook.
    """
    review_count: int
    correct_count: int
    incorrect_count: int
    avg_response_time_s: float
    days_since_last_review: float
    question_difficulty: float  # 0.0 (easy) – 1.0 (hard), from SM-2 easiness


class RetentionPredictor:
    """
    Singleton wrapper around the loaded sklearn model.
    Usage:
        probability = RetentionPredictor.predict(features)
    """
    _model = None
    _loaded = False

    @classmethod
    def load(cls) -> None:
        """
        Load the joblib model file at application startup.
        Silently skips if the file doesn't exist — Phase 1–5 will use the heuristic fallback.
        """
        if not os.path.exists(_MODEL_PATH):
            logger.info(
                f"Retention model not found at {_MODEL_PATH}. "
                "Using SM-2 heuristic until Phase 6 model is trained and exported."
            )
            cls._loaded = False
            return

        try:
            import joblib
            cls._model = joblib.load(_MODEL_PATH)
            cls._loaded = True
            logger.info(f"Retention model loaded from {_MODEL_PATH}")
        except Exception as exc:
            logger.error(f"Failed to load retention model: {exc}. Falling back to heuristic.")
            cls._loaded = False

    @classmethod
    def predict(cls, features: RetentionFeatures) -> float:
        """
        Predict the probability that a student still remembers a flashcard today.

        Returns a float in [0.0, 1.0].

        If the ML model is loaded (Phase 6+): uses GBR prediction → converts
        predicted half-life to recall probability via the Ebbinghaus formula.

        If the model is not loaded (Phase 1–5): falls back to a heuristic based
        on the Ebbinghaus curve with parameters estimated from SM-2 easiness.
        """
        if cls._loaded and cls._model is not None:
            return cls._predict_with_model(features)
        else:
            return cls._heuristic_predict(features)

    @classmethod
    def _predict_with_model(cls, features: RetentionFeatures) -> float:
        """
        Use the trained GBR to predict half-life (in log1p space), then
        invert with expm1 to get real-scale days, then convert to recall
        probability via the Duolingo HLR formula: P = 2^(-t / h).

        The model was trained on log1p(half_life) targets (v2), so the raw
        model output is in log-space and must be inverted before use.
        """
        import numpy as np

        X = [[
            features.review_count,
            features.correct_count,
            features.incorrect_count,
            features.avg_response_time_s,
            features.days_since_last_review,
            features.question_difficulty,
        ]]
        # Model predicts log1p(half_life) — invert to get days
        log_half_life = float(cls._model.predict(X)[0])
        half_life = math.expm1(log_half_life)         # expm1(x) = exp(x) - 1
        half_life = max(0.1, half_life)               # floor: prevents division by tiny/zero h

        # Duolingo HLR formula: P(recall) = 2^(-t/h)
        # where t = elapsed days since last review, h = memory half-life in days
        t = features.days_since_last_review
        probability = 2 ** (-t / half_life)
        return round(max(0.0, min(1.0, probability)), 4)

    @classmethod
    def _heuristic_predict(cls, features: RetentionFeatures) -> float:
        """
        Fallback heuristic before the Phase 6 model is trained.
        Uses a simplified Ebbinghaus curve where memory strength is estimated
        from the SM-2 easiness factor (inverse of difficulty) and review count.
        """
        if features.days_since_last_review <= 0:
            return 1.0  # just reviewed — perfect recall assumed

        # Estimate memory strength from review history
        # More reviews and higher accuracy → stronger memory → longer half-life
        accuracy = (features.correct_count / features.review_count
                    if features.review_count > 0 else 0.5)
        base_strength = 1.0 - features.question_difficulty  # 0 = hard, 1 = easy
        strength = base_strength * (0.5 + 0.5 * accuracy) * (1 + 0.2 * features.review_count)

        # Convert to probability using exponential decay
        # Larger strength → slower decay
        probability = math.exp(-features.days_since_last_review / max(0.5, strength * 10))
        return round(max(0.0, min(1.0, probability)), 4)
