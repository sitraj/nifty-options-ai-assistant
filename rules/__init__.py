"""Rule engine for option trading signals."""

from rules.engine import (
    EvaluationResult,
    RuleResult,
    SignalResult,
    evaluate,
    evaluate_rules,
)
from rules.explainer import (
    Explanation,
    explain,
)
from rules.safety import (
    SafetyResult,
    check_safety,
)
from rules.scoring import (
    ScoreResult,
    calculate_score,
    get_default_weights,
    get_score_thresholds,
)

__all__ = [
    "EvaluationResult",
    "Explanation",
    "RuleResult",
    "SafetyResult",
    "ScoreResult",
    "SignalResult",
    "calculate_score",
    "check_safety",
    "evaluate",
    "evaluate_rules",
    "explain",
    "get_default_weights",
    "get_score_thresholds",
]
