"""Scoring engine for combining rule outputs with configurable weights."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from rules.engine import RuleResult


@dataclass
class ScoreResult:
    """Result from scoring engine."""

    final_score: float  # Between -1 and +1
    category: str  # "Strong Bullish", "Mild Bullish", "Neutral", "Mild Bearish", "Strong Bearish"
    weighted_contributions: Dict[str, float]  # Rule name -> weighted contribution
    weights_used: Dict[str, float]  # Rule name -> weight used


# Default weights for rules
DEFAULT_WEIGHTS = {
    "PCR Rule": 0.4,
    "OI Build-up Rule": 0.2,
    "Max OI Rule": 0.2,
    "Support/Resistance Rule": 0.2,
}

# Score category thresholds
SCORE_THRESHOLDS = {
    "strong_bullish": 0.6,  # score >= 0.6
    "mild_bullish": 0.2,  # 0.2 <= score < 0.6
    "neutral": -0.2,  # -0.2 < score < 0.2
    "mild_bearish": -0.6,  # -0.6 < score <= -0.2
    # score <= -0.6 = strong_bearish
}


def _normalize_weights(weights: Dict[str, float]) -> Dict[str, float]:
    """Normalize weights to sum to 1.0.

    Args:
        weights: Dictionary of rule names to weights.

    Returns:
        Normalized weights dictionary.
    """
    total = sum(weights.values())
    if total == 0:
        # If all weights are zero, return equal weights
        num_rules = len(weights)
        return {name: 1.0 / num_rules if num_rules > 0 else 0.0 for name in weights}

    return {name: weight / total for name, weight in weights.items()}


def _map_score_to_category(score: float) -> str:
    """Map numerical score to category.

    Args:
        score: Final score between -1 and +1.

    Returns:
        Category string.
    """
    if score >= SCORE_THRESHOLDS["strong_bullish"]:
        return "Strong Bullish"
    elif score >= SCORE_THRESHOLDS["mild_bullish"]:
        return "Mild Bullish"
    elif score > SCORE_THRESHOLDS["neutral"]:
        return "Neutral"
    elif score > SCORE_THRESHOLDS["mild_bearish"]:
        return "Mild Bearish"
    else:
        return "Strong Bearish"


def calculate_score(
    rule_results: List[RuleResult],
    weights: Dict[str, float] | None = None,
) -> ScoreResult:
    """Calculate weighted score from rule results.

    Combines individual rule signal strengths using configurable weights
    to produce a final score between -1 and +1, then maps it to a category.

    Args:
        rule_results: List of RuleResult objects from rule evaluation.
        weights: Optional dictionary mapping rule names to weights.
                 If None, uses DEFAULT_WEIGHTS.
                 Weights will be normalized to sum to 1.0.

    Returns:
        ScoreResult with:
            - final_score: Weighted score between -1 and +1
            - category: "Strong Bullish", "Mild Bullish", "Neutral",
                       "Mild Bearish", or "Strong Bearish"
            - weighted_contributions: Individual rule contributions
            - weights_used: Normalized weights applied

    Raises:
        ValueError: If rule_results is empty or weights don't match rules.
    """
    if not rule_results:
        raise ValueError("rule_results cannot be empty")

    # Use default weights if not provided
    if weights is None:
        weights = DEFAULT_WEIGHTS.copy()
    else:
        weights = weights.copy()

    # Get rule names from results
    rule_names = [result.name for result in rule_results]

    # Ensure all rules in results have weights
    for rule_name in rule_names:
        if rule_name not in weights:
            # Use default weight if available, otherwise 0
            if rule_name in DEFAULT_WEIGHTS:
                weights[rule_name] = DEFAULT_WEIGHTS[rule_name]
            else:
                weights[rule_name] = 0.0

    # Remove weights for rules not in results
    weights = {name: weights[name] for name in rule_names if name in weights}

    # Normalize weights
    normalized_weights = _normalize_weights(weights)

    # Calculate weighted contributions
    weighted_contributions = {}
    final_score = 0.0

    for result in rule_results:
        rule_name = result.name
        weight = normalized_weights.get(rule_name, 0.0)
        signal_strength = result.signal_strength

        # Calculate contribution (weight * signal_strength)
        contribution = weight * signal_strength
        weighted_contributions[rule_name] = contribution
        final_score += contribution

    # Clamp final score to [-1, 1]
    final_score = max(-1.0, min(1.0, final_score))

    # Map to category
    category = _map_score_to_category(final_score)

    return ScoreResult(
        final_score=final_score,
        category=category,
        weighted_contributions=weighted_contributions,
        weights_used=normalized_weights,
    )


def get_default_weights() -> Dict[str, float]:
    """Get default weights for rules.

    Returns:
        Dictionary of default weights.
    """
    return DEFAULT_WEIGHTS.copy()


def get_score_thresholds() -> Dict[str, float]:
    """Get score category thresholds.

    Returns:
        Dictionary of threshold values for score categories.
    """
    return SCORE_THRESHOLDS.copy()
