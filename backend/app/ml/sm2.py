"""
SM-2 Spaced Repetition Algorithm — implementation from scratch.

─── What is spaced repetition? ───────────────────────────────────────────────
The human brain forgets information exponentially over time (Ebbinghaus
forgetting curve). Spaced repetition exploits this by scheduling reviews
just before you would forget — the "spacing effect" shows that memories
reinforced at expanding intervals are retained much more efficiently than
massed (cramming) study.

─── The SM-2 Algorithm ───────────────────────────────────────────────────────
SM-2 was developed by Piotr Wozniak in 1987 and is the basis for the popular
flashcard app Anki. It works as follows:

State per card (stored in the flashcard row):
  interval (I):      days until the next review
  repetitions (n):   count of consecutive correct reviews
  easiness (EF):     E-factor multiplier, starts at 2.5, minimum 1.3

On each review, the student rates their recall quality (q) on a scale 0–5:
  5 = perfect response, no hesitation
  4 = correct after slight hesitation
  3 = correct with significant difficulty
  2 = incorrect — correct answer easy to recognise on seeing it
  1 = incorrect — correct answer hard to recall
  0 = total blackout

Algorithm steps:
  1. If q < 3 (failed): reset n = 0, I = 1. The card is due tomorrow.
  2. If q ≥ 3 (passed):
       - n = 0: I = 1 (first correct review — review again tomorrow)
       - n = 1: I = 6 (second correct review — review in 6 days)
       - n > 1: I = round(I_prev × EF)
       After computing I, increment n by 1.
  3. Update EF: EF = EF + (0.1 - (5 - q) × (0.08 + (5 - q) × 0.02))
     Clamp EF to minimum 1.3 (prevents cards from being scheduled too far out).

Key insight for the viva:
  The EF decreases if quality < 5 (the more you struggle, the shorter
  the next interval) and increases if quality = 5 (the easier the card,
  the longer the gap grows). This is adaptive difficulty.

Phase 6 extension:
  In Phase 6, we additionally compute a Half-Life Regression prediction
  (probability you'll still remember this card on the scheduled review day).
  If that probability is too low, we can preemptively shorten the interval.
  SM-2 remains as the baseline; the ML model is a second signal.
"""

from datetime import datetime, timedelta, timezone
from dataclasses import dataclass


@dataclass
class SM2State:
    interval: int      # days until next review
    repetitions: int   # consecutive correct reviews
    easiness: float    # E-factor (≥ 1.3)


def sm2_update(state: SM2State, quality: int) -> SM2State:
    """
    Apply one SM-2 review and return the updated state.

    Args:
        state:   Current SM-2 state for this flashcard.
        quality: Student's self-rated recall quality, integer 0–5.

    Returns:
        A new SM2State with updated interval, repetitions, and easiness.
    """
    if not 0 <= quality <= 5:
        raise ValueError(f"SM-2 quality must be 0–5, got {quality}")

    # ── Step 1: Update EF ────────────────────────────────────────────────────
    # This formula is the canonical SM-2 EF update. When q = 5 (perfect), EF
    # increases by 0.1. When q = 3 (barely correct), EF is unchanged.
    # When q < 3, EF decreases (card is getting harder in the student's model).
    new_easiness = state.easiness + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_easiness = max(1.3, new_easiness)  # EF floor = 1.3 (Wozniak's original constraint)

    # ── Step 2: Update interval and repetitions ───────────────────────────────
    if quality < 3:
        # Failed recall — start over. Review again tomorrow.
        new_interval = 1
        new_repetitions = 0
    else:
        # Passed recall — advance along the exponential growth curve.
        if state.repetitions == 0:
            new_interval = 1       # first ever correct review
        elif state.repetitions == 1:
            new_interval = 6       # second correct review — short jump to a week
        else:
            # Beyond second review: multiply previous interval by E-factor
            # This creates the exponential growth characteristic of spaced repetition
            new_interval = round(state.interval * new_easiness)

        new_repetitions = state.repetitions + 1

    return SM2State(
        interval=new_interval,
        repetitions=new_repetitions,
        easiness=new_easiness,
    )


def next_review_datetime(interval_days: int) -> datetime:
    """
    Compute the next review datetime: now + interval_days, at midnight UTC.
    Cards are due at the start of the review day, not at a specific time.
    """
    return (
        datetime.now(timezone.utc)
        + timedelta(days=interval_days)
    ).replace(hour=0, minute=0, second=0, microsecond=0)


def difficulty_from_easiness(easiness: float) -> float:
    """
    Convert SM-2 E-factor to a 0–1 difficulty score (used as a feature
    for the Phase 6 retention model).
    EF range is 1.3 (hard) to ~3.5+ (very easy).
    Maps to difficulty: 1.0 (EF=1.3) → 0.0 (EF=2.5, default) → negative (EF>2.5).
    We clamp to [0, 1].
    """
    # Linear mapping: EF=1.3 → 1.0 difficulty, EF=2.5 → 0.0 difficulty
    difficulty = max(0.0, min(1.0, 1.0 - (easiness - 1.3) / (2.5 - 1.3)))
    return round(difficulty, 4)
