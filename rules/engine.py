"""Rule engine for beginner-friendly option buying signals."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class RuleResult:
    """Result of a single rule evaluation."""

    name: str
    description: str
    signal_strength: float  # Between -1 and +1
    triggered: bool
    explanation: str


@dataclass
class SignalResult:
    """Overall signal result from rule engine."""

    overall_signal: float  # Between -1 and +1
    bias: str  # "Bullish", "Bearish", "Sideways", "No-Trade"
    risk_warning: bool
    risk_reasons: List[str]
    rule_results: List[RuleResult]
    recommendation: str


# Rule thresholds - beginner-friendly values
_THRESHOLDS = {
    # PCR thresholds
    "pcr_very_bullish": 1.5,  # PCR > 1.5 = very bullish
    "pcr_bullish": 1.2,  # PCR > 1.2 = bullish
    "pcr_neutral_high": 1.0,  # PCR > 1.0 = slightly bullish
    "pcr_neutral_low": 0.8,  # PCR < 0.8 = slightly bearish
    "pcr_bearish": 0.6,  # PCR < 0.6 = bearish
    "pcr_very_bearish": 0.4,  # PCR < 0.4 = very bearish
    "pcr_extreme_high": 2.0,  # PCR > 2.0 = extreme (risk)
    "pcr_extreme_low": 0.3,  # PCR < 0.3 = extreme (risk)
    # OI build-up thresholds
    "oi_long_threshold": 0.1,  # Positive OI change threshold
    "oi_short_threshold": -0.1,  # Negative OI change threshold
    # Signal strength thresholds
    "strong_signal": 0.6,  # |signal| > 0.6 = strong
    "moderate_signal": 0.3,  # |signal| > 0.3 = moderate
    "weak_signal": 0.1,  # |signal| > 0.1 = weak
}


def _evaluate_pcr_rule(overall_pcr: float | None) -> RuleResult:
    """Evaluate Put-Call Ratio rule for market bias.

    High PCR (>1.0) suggests bullish sentiment (more puts = protection).
    Low PCR (<1.0) suggests bearish sentiment (more calls = upside bets).

    Args:
        overall_pcr: Overall Put-Call Ratio.

    Returns:
        RuleResult with PCR-based signal.
    """
    if overall_pcr is None:
        return RuleResult(
            name="PCR Rule",
            description="Put-Call Ratio indicates market sentiment",
            signal_strength=0.0,
            triggered=False,
            explanation="PCR data not available",
        )

    # Calculate signal strength based on PCR
    if overall_pcr >= _THRESHOLDS["pcr_very_bullish"]:
        if overall_pcr >= _THRESHOLDS["pcr_extreme_high"]:
            signal = 0.9
            explanation = f"Extremely high PCR ({overall_pcr:.2f}) - Very bullish but high risk"
        else:
            signal = 0.8
            explanation = f"Very high PCR ({overall_pcr:.2f}) - Strong bullish sentiment"
    elif overall_pcr >= _THRESHOLDS["pcr_bullish"]:
        signal = 0.6
        explanation = f"High PCR ({overall_pcr:.2f}) - Bullish sentiment"
    elif overall_pcr >= _THRESHOLDS["pcr_neutral_high"]:
        signal = 0.3
        explanation = f"PCR above 1.0 ({overall_pcr:.2f}) - Slightly bullish"
    elif overall_pcr >= _THRESHOLDS["pcr_neutral_low"]:
        signal = 0.0
        explanation = f"Neutral PCR ({overall_pcr:.2f}) - Balanced market"
    elif overall_pcr >= _THRESHOLDS["pcr_bearish"]:
        signal = -0.3
        explanation = f"PCR below 1.0 ({overall_pcr:.2f}) - Slightly bearish"
    elif overall_pcr >= _THRESHOLDS["pcr_very_bearish"]:
        signal = -0.6
        explanation = f"Low PCR ({overall_pcr:.2f}) - Bearish sentiment"
    else:
        if overall_pcr <= _THRESHOLDS["pcr_extreme_low"]:
            signal = -0.9
            explanation = f"Extremely low PCR ({overall_pcr:.2f}) - Very bearish but high risk"
        else:
            signal = -0.8
            explanation = f"Very low PCR ({overall_pcr:.2f}) - Strong bearish sentiment"

    return RuleResult(
        name="PCR Rule",
        description="Put-Call Ratio indicates market sentiment (PCR > 1.0 = bullish, < 1.0 = bearish)",
        signal_strength=signal,
        triggered=True,
        explanation=explanation,
    )


def _evaluate_oi_buildup_rule(oi_buildup_type: str) -> RuleResult:
    """Evaluate OI build-up type rule.

    Long build-up (both increasing) = strong directional move expected.
    Short build-up (both decreasing) = position covering, uncertainty.
    Unwinding = mixed signals, sideways likely.

    Args:
        oi_buildup_type: OI build-up type from features.

    Returns:
        RuleResult with OI build-up based signal.
    """
    if oi_buildup_type == "Unknown":
        return RuleResult(
            name="OI Build-up Rule",
            description="Open Interest build-up indicates position strength",
            signal_strength=0.0,
            triggered=False,
            explanation="OI build-up data not available",
        )

    if oi_buildup_type == "Long":
        return RuleResult(
            name="OI Build-up Rule",
            description="Both Call and Put OI increasing - Strong directional move expected",
            signal_strength=0.5,
            triggered=True,
            explanation="Long build-up: Both call and put OI increasing, indicating strong positions",
        )
    elif oi_buildup_type == "Short":
        return RuleResult(
            name="OI Build-up Rule",
            description="Both Call and Put OI decreasing - Position covering, uncertainty",
            signal_strength=-0.2,
            triggered=True,
            explanation="Short build-up: Both call and put OI decreasing, positions being covered",
        )
    elif oi_buildup_type == "Unwinding":
        return RuleResult(
            name="OI Build-up Rule",
            description="Mixed OI changes - Sideways movement likely",
            signal_strength=0.0,
            triggered=True,
            explanation="Unwinding: Mixed OI changes suggest sideways movement",
        )
    else:  # Mixed
        return RuleResult(
            name="OI Build-up Rule",
            description="Inconsistent OI pattern - Unclear direction",
            signal_strength=0.0,
            triggered=True,
            explanation="Mixed pattern: Inconsistent OI changes, unclear direction",
        )


def _evaluate_max_oi_rule(
    max_call_oi_strike: float | None,
    max_put_oi_strike: float | None,
    underlying_value: float | None,
    atm_strike: float | None,
) -> RuleResult:
    """Evaluate Max OI strikes rule.

    Max Put OI below current price = support level (bullish).
    Max Call OI above current price = resistance level (bearish).

    Args:
        max_call_oi_strike: Strike with maximum call OI.
        max_put_oi_strike: Strike with maximum put OI.
        underlying_value: Current underlying price.
        atm_strike: ATM strike price.

    Returns:
        RuleResult with Max OI based signal.
    """
    if underlying_value is None or atm_strike is None:
        return RuleResult(
            name="Max OI Rule",
            description="Maximum OI strikes indicate support/resistance levels",
            signal_strength=0.0,
            triggered=False,
            explanation="Underlying or ATM data not available",
        )

    signal = 0.0
    explanations = []

    # Analyze max put OI position (support)
    if max_put_oi_strike is not None:
        if max_put_oi_strike < underlying_value:
            # Max put OI below = strong support = bullish
            distance_pct = ((underlying_value - max_put_oi_strike) / underlying_value) * 100
            if distance_pct > 2.0:
                signal += 0.4
                explanations.append(
                    f"Max Put OI at {max_put_oi_strike:.0f} (support {distance_pct:.1f}% below)"
                )
            else:
                signal += 0.2
                explanations.append(
                    f"Max Put OI at {max_put_oi_strike:.0f} (near support)"
                )
        elif max_put_oi_strike > underlying_value:
            # Max put OI above = bearish
            distance_pct = ((max_put_oi_strike - underlying_value) / underlying_value) * 100
            if distance_pct > 2.0:
                signal -= 0.3
                explanations.append(
                    f"Max Put OI at {max_put_oi_strike:.0f} (above price, bearish)"
                )
            else:
                signal -= 0.1
                explanations.append(
                    f"Max Put OI at {max_put_oi_strike:.0f} (slightly above)"
                )

    # Analyze max call OI position (resistance)
    if max_call_oi_strike is not None:
        if max_call_oi_strike > underlying_value:
            # Max call OI above = resistance = bearish
            distance_pct = ((max_call_oi_strike - underlying_value) / underlying_value) * 100
            if distance_pct > 2.0:
                signal -= 0.4
                explanations.append(
                    f"Max Call OI at {max_call_oi_strike:.0f} (resistance {distance_pct:.1f}% above)"
                )
            else:
                signal -= 0.2
                explanations.append(
                    f"Max Call OI at {max_call_oi_strike:.0f} (near resistance)"
                )
        elif max_call_oi_strike < underlying_value:
            # Max call OI below = bullish
            distance_pct = ((underlying_value - max_call_oi_strike) / underlying_value) * 100
            if distance_pct > 2.0:
                signal += 0.3
                explanations.append(
                    f"Max Call OI at {max_call_oi_strike:.0f} (below price, bullish)"
                )
            else:
                signal += 0.1
                explanations.append(
                    f"Max Call OI at {max_call_oi_strike:.0f} (slightly below)"
                )

    explanation = "; ".join(explanations) if explanations else "Max OI data not available"

    return RuleResult(
        name="Max OI Rule",
        description="Maximum OI strikes indicate key support/resistance levels",
        signal_strength=max(-1.0, min(1.0, signal)),  # Clamp to [-1, 1]
        triggered=len(explanations) > 0,
        explanation=explanation,
    )


def _evaluate_support_resistance_rule(
    support: float | None,
    resistance: float | None,
    underlying_value: float | None,
) -> RuleResult:
    """Evaluate support and resistance levels rule.

    Strong support close to price = bullish.
    Strong resistance close to price = bearish.
    Price between support and resistance = sideways.

    Args:
        support: Support level from features.
        resistance: Resistance level from features.
        underlying_value: Current underlying price.

    Returns:
        RuleResult with support/resistance based signal.
    """
    if underlying_value is None:
        return RuleResult(
            name="Support/Resistance Rule",
            description="Support and resistance levels indicate price boundaries",
            signal_strength=0.0,
            triggered=False,
            explanation="Underlying price not available",
        )

    signal = 0.0
    explanations = []

    # Analyze support
    if support is not None:
        distance_pct = ((underlying_value - support) / underlying_value) * 100
        if distance_pct < 1.0:
            signal += 0.3
            explanations.append(f"Strong support at {support:.0f} (very close)")
        elif distance_pct < 2.0:
            signal += 0.2
            explanations.append(f"Support at {support:.0f} ({distance_pct:.1f}% below)")
        else:
            explanations.append(f"Support at {support:.0f} ({distance_pct:.1f}% below)")

    # Analyze resistance
    if resistance is not None:
        distance_pct = ((resistance - underlying_value) / underlying_value) * 100
        if distance_pct < 1.0:
            signal -= 0.3
            explanations.append(f"Strong resistance at {resistance:.0f} (very close)")
        elif distance_pct < 2.0:
            signal -= 0.2
            explanations.append(f"Resistance at {resistance:.0f} ({distance_pct:.1f}% above)")
        else:
            explanations.append(f"Resistance at {resistance:.0f} ({distance_pct:.1f}% above)")

    # Sideways scenario
    if support is not None and resistance is not None:
        support_distance = ((underlying_value - support) / underlying_value) * 100
        resistance_distance = ((resistance - underlying_value) / underlying_value) * 100
        if support_distance < 2.0 and resistance_distance < 2.0:
            signal = 0.0
            explanations.append("Price between support and resistance - Sideways movement likely")

    explanation = "; ".join(explanations) if explanations else "Support/resistance data not available"

    return RuleResult(
        name="Support/Resistance Rule",
        description="Support and resistance levels indicate price boundaries",
        signal_strength=max(-1.0, min(1.0, signal)),  # Clamp to [-1, 1]
        triggered=len(explanations) > 0,
        explanation=explanation,
    )


def _check_risk_warnings(features: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Check for high-risk warning conditions.

    Args:
        features: Dictionary of calculated features.

    Returns:
        Tuple of (has_risk_warning, list_of_reasons).
    """
    risk_reasons = []
    has_risk = False

    # Extreme PCR check
    overall_pcr = features.get("overall_pcr")
    if overall_pcr is not None:
        if overall_pcr >= _THRESHOLDS["pcr_extreme_high"]:
            has_risk = True
            risk_reasons.append(
                f"Extreme PCR ({overall_pcr:.2f}) - Market may be overbought, high reversal risk"
            )
        elif overall_pcr <= _THRESHOLDS["pcr_extreme_low"]:
            has_risk = True
            risk_reasons.append(
                f"Extreme PCR ({overall_pcr:.2f}) - Market may be oversold, high reversal risk"
            )

    # Missing critical data
    if features.get("overall_pcr") is None:
        risk_reasons.append("PCR data missing - Incomplete analysis")
        has_risk = True

    if features.get("underlying_value") is None:
        risk_reasons.append("Underlying price missing - Position sizing difficult")

    # Unwinding or mixed OI
    oi_type = features.get("oi_buildup_type", "")
    if oi_type in ["Unwinding", "Mixed"]:
        risk_reasons.append(f"OI pattern ({oi_type}) - Unclear direction, higher risk")

    return has_risk, risk_reasons


def evaluate_rules(features: Dict[str, Any]) -> SignalResult:
    """Evaluate all rules and generate trading signal.

    Args:
        features: Dictionary from calculate_features() containing:
            - overall_pcr
            - oi_buildup_type
            - max_call_oi_strike
            - max_put_oi_strike
            - support
            - resistance
            - underlying_value
            - atm_strike

    Returns:
        SignalResult with overall signal, bias, warnings, and explanations.
    """
    # Evaluate all rules
    rule_results = []

    # PCR Rule
    pcr_result = _evaluate_pcr_rule(features.get("overall_pcr"))
    rule_results.append(pcr_result)

    # OI Build-up Rule
    oi_result = _evaluate_oi_buildup_rule(features.get("oi_buildup_type", "Unknown"))
    rule_results.append(oi_result)

    # Max OI Rule
    max_oi_result = _evaluate_max_oi_rule(
        features.get("max_call_oi_strike"),
        features.get("max_put_oi_strike"),
        features.get("underlying_value"),
        features.get("atm_strike"),
    )
    rule_results.append(max_oi_result)

    # Support/Resistance Rule
    sr_result = _evaluate_support_resistance_rule(
        features.get("support"),
        features.get("resistance"),
        features.get("underlying_value"),
    )
    rule_results.append(sr_result)

    # Calculate weighted overall signal
    # PCR gets highest weight (40%), others get 20% each
    weights = [0.4, 0.2, 0.2, 0.2]
    overall_signal = sum(
        result.signal_strength * weight
        for result, weight in zip(rule_results, weights)
    )
    overall_signal = max(-1.0, min(1.0, overall_signal))  # Clamp to [-1, 1]

    # Determine bias
    if abs(overall_signal) < _THRESHOLDS["weak_signal"]:
        bias = "No-Trade"
        recommendation = "Market conditions unclear. Wait for clearer signals before trading."
    elif abs(overall_signal) < _THRESHOLDS["moderate_signal"]:
        bias = "Sideways"
        recommendation = "Weak directional signal. Consider staying out or using range-bound strategies."
    elif overall_signal > 0:
        bias = "Bullish"
        if abs(overall_signal) >= _THRESHOLDS["strong_signal"]:
            recommendation = "Strong bullish signal. Consider buying call options with proper risk management."
        else:
            recommendation = "Moderate bullish signal. Consider buying call options with caution."
    else:
        bias = "Bearish"
        if abs(overall_signal) >= _THRESHOLDS["strong_signal"]:
            recommendation = "Strong bearish signal. Consider buying put options with proper risk management."
        else:
            recommendation = "Moderate bearish signal. Consider buying put options with caution."

    # Check for risk warnings
    has_risk, risk_reasons = _check_risk_warnings(features)

    if has_risk:
        recommendation += " WARNING: High-risk conditions detected. Reduce position size and use strict stop-loss."

    return SignalResult(
        overall_signal=overall_signal,
        bias=bias,
        risk_warning=has_risk,
        risk_reasons=risk_reasons,
        rule_results=rule_results,
        recommendation=recommendation,
    )


@dataclass
class EvaluationResult:
    """Result from rule evaluator with structured outputs."""

    market_bias: str  # "Bullish", "Bearish", "Sideways", "No-Trade"
    confidence_score: float  # 0.0 to 1.0 (0% to 100%)
    risk_level: str  # "Low", "Medium", "High"
    trade_recommendation: str  # "Call", "Put", "No Trade"
    signal_strength: float  # -1.0 to +1.0
    risk_reasons: List[str]
    rule_results: List[RuleResult]


def _calculate_confidence_score(
    overall_signal: float,
    rule_results: List[RuleResult],
) -> float:
    """Calculate confidence score based on signal strength and rule agreement.

    Args:
        overall_signal: Overall signal strength (-1 to +1).
        rule_results: List of individual rule results.

    Returns:
        Confidence score between 0.0 and 1.0.
    """
    # Base confidence from signal strength magnitude
    signal_magnitude = abs(overall_signal)
    base_confidence = signal_magnitude

    # Calculate rule agreement (how many rules agree with the direction)
    if len(rule_results) == 0:
        return 0.0

    triggered_rules = [r for r in rule_results if r.triggered]
    if len(triggered_rules) == 0:
        return 0.0

    # Count rules that agree with overall signal direction
    if overall_signal > 0:
        agreeing_rules = sum(
            1 for r in triggered_rules if r.signal_strength > 0
        )
    elif overall_signal < 0:
        agreeing_rules = sum(
            1 for r in triggered_rules if r.signal_strength < 0
        )
    else:
        agreeing_rules = sum(
            1 for r in triggered_rules if abs(r.signal_strength) < 0.1
        )

    agreement_ratio = agreeing_rules / len(triggered_rules) if triggered_rules else 0.0

    # Calculate average rule strength magnitude
    avg_rule_strength = sum(abs(r.signal_strength) for r in triggered_rules) / len(triggered_rules) if triggered_rules else 0.0

    # Combine factors: signal strength (50%), agreement (30%), rule strength (20%)
    confidence = (
        base_confidence * 0.5
        + agreement_ratio * 0.3
        + avg_rule_strength * 0.2
    )

    return min(1.0, max(0.0, confidence))


def _determine_risk_level(
    has_risk_warning: bool,
    risk_reasons: List[str],
    overall_signal: float,
    confidence_score: float,
) -> str:
    """Determine risk level based on warnings and signal quality.

    Args:
        has_risk_warning: Whether risk warnings were triggered.
        risk_reasons: List of risk reasons.
        overall_signal: Overall signal strength.
        confidence_score: Confidence score.

    Returns:
        Risk level: "Low", "Medium", or "High".
    """
    # High risk conditions
    if has_risk_warning:
        # Count critical risk factors
        critical_risks = sum(
            1 for reason in risk_reasons
            if "extreme" in reason.lower() or "missing" in reason.lower()
        )
        if critical_risks >= 2:
            return "High"
        elif critical_risks >= 1 or len(risk_reasons) >= 2:
            return "High"
        else:
            return "Medium"

    # Low confidence = higher risk
    if confidence_score < 0.3:
        return "Medium"

    # Weak signal = medium risk
    if abs(overall_signal) < _THRESHOLDS["moderate_signal"]:
        return "Medium"

    # Strong signal with good confidence = low risk
    if abs(overall_signal) >= _THRESHOLDS["strong_signal"] and confidence_score >= 0.6:
        return "Low"

    # Default to medium risk
    return "Medium"


def _determine_trade_recommendation(
    bias: str,
    overall_signal: float,
    confidence_score: float,
) -> str:
    """Determine trade recommendation based on bias and confidence.

    Args:
        bias: Market bias from rule evaluation.
        overall_signal: Overall signal strength.
        confidence_score: Confidence score.

    Returns:
        Trade recommendation: "Call", "Put", or "No Trade".
    """
    # No trade conditions
    if bias in ["No-Trade", "Sideways"]:
        return "No Trade"

    if abs(overall_signal) < _THRESHOLDS["weak_signal"]:
        return "No Trade"

    if confidence_score < 0.2:
        return "No Trade"

    # Trade recommendations based on bias
    if bias == "Bullish":
        return "Call"
    elif bias == "Bearish":
        return "Put"
    else:
        return "No Trade"


def evaluate(features: Dict[str, Any]) -> EvaluationResult:
    """Rule evaluator that produces structured trading outputs.

    This function accepts engineered metrics, runs all rules, and produces
    a clean evaluation result with market bias, confidence score, risk level,
    and trade recommendation.

    Args:
        features: Dictionary from calculate_features() containing:
            - overall_pcr
            - oi_buildup_type
            - max_call_oi_strike
            - max_put_oi_strike
            - support
            - resistance
            - underlying_value
            - atm_strike

    Returns:
        EvaluationResult with:
            - market_bias: "Bullish", "Bearish", "Sideways", or "No-Trade"
            - confidence_score: 0.0 to 1.0 (0% to 100%)
            - risk_level: "Low", "Medium", or "High"
            - trade_recommendation: "Call", "Put", or "No Trade"
            - signal_strength: -1.0 to +1.0
            - risk_reasons: List of risk warnings
            - rule_results: Individual rule evaluation results
    """
    # Run all rules
    signal_result = evaluate_rules(features)

    # Calculate confidence score
    confidence_score = _calculate_confidence_score(
        signal_result.overall_signal,
        signal_result.rule_results,
    )

    # Determine risk level
    risk_level = _determine_risk_level(
        signal_result.risk_warning,
        signal_result.risk_reasons,
        signal_result.overall_signal,
        confidence_score,
    )

    # Determine trade recommendation
    trade_recommendation = _determine_trade_recommendation(
        signal_result.bias,
        signal_result.overall_signal,
        confidence_score,
    )

    return EvaluationResult(
        market_bias=signal_result.bias,
        confidence_score=confidence_score,
        risk_level=risk_level,
        trade_recommendation=trade_recommendation,
        signal_strength=signal_result.overall_signal,
        risk_reasons=signal_result.risk_reasons,
        rule_results=signal_result.rule_results,
    )
