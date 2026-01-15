"""Convert technical signals into beginner-friendly explanations."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from rules.engine import EvaluationResult
from rules.safety import SafetyResult
from rules.scoring import ScoreResult


@dataclass
class Explanation:
    """Beginner-friendly explanation of trading signals."""

    market_bias: str
    suggested_action: str
    why: List[str]  # Bullet points explaining the reasoning
    risk_level: str
    what_can_go_wrong: List[str]  # Potential risks explained simply


def _explain_market_bias(
    evaluation: EvaluationResult,
    score_result: ScoreResult | None = None,
) -> str:
    """Explain market bias in beginner-friendly terms.

    Args:
        evaluation: Evaluation result from rule engine.
        score_result: Optional score result for additional context.

    Returns:
        Beginner-friendly market bias explanation.
    """
    bias = evaluation.market_bias

    if score_result:
        category = score_result.category
        if category == "Strong Bullish":
            return "The market shows strong upward momentum. Multiple indicators suggest prices may rise."
        elif category == "Mild Bullish":
            return "The market shows moderate upward momentum. There's a slight preference for price increases."
        elif category == "Strong Bearish":
            return "The market shows strong downward momentum. Multiple indicators suggest prices may fall."
        elif category == "Mild Bearish":
            return "The market shows moderate downward momentum. There's a slight preference for price decreases."
        elif category == "Neutral":
            return "The market shows mixed signals. There's no clear directional bias at the moment."

    # Fallback to evaluation bias
    if bias == "Bullish":
        return "The market shows upward momentum. Indicators suggest prices may rise."
    elif bias == "Bearish":
        return "The market shows downward momentum. Indicators suggest prices may fall."
    elif bias == "Sideways":
        return "The market shows mixed signals. Prices may move within a range."
    else:  # No-Trade
        return "The market signals are unclear. There's no strong directional bias."


def _explain_suggested_action(
    evaluation: EvaluationResult,
    safety: SafetyResult | None = None,
) -> str:
    """Explain suggested action in beginner-friendly terms.

    Args:
        evaluation: Evaluation result from rule engine.
        safety: Optional safety result to check for blocks.

    Returns:
        Beginner-friendly action recommendation.
    """
    # Check if trading is blocked
    if safety and safety.blocked:
        return (
            "Trading is not recommended at this time. Safety checks have identified "
            "conditions that are not suitable for beginners. Please wait for better market conditions."
        )

    trade_rec = evaluation.trade_recommendation
    confidence = evaluation.confidence_score
    risk_level = evaluation.risk_level

    if trade_rec == "Call":
        if confidence >= 0.7 and risk_level == "Low":
            return (
                "Consider buying call options if you understand the risks. "
                "The signals are relatively strong, but remember that options can expire worthless."
            )
        elif confidence >= 0.5:
            return (
                "You may consider buying call options, but use caution. "
                "The signals are moderate, so consider smaller position sizes."
            )
        else:
            return (
                "Call options are possible but not strongly recommended. "
                "The signals are weak, and the risk may outweigh potential rewards."
            )
    elif trade_rec == "Put":
        if confidence >= 0.7 and risk_level == "Low":
            return (
                "Consider buying put options if you understand the risks. "
                "The signals are relatively strong, but remember that options can expire worthless."
            )
        elif confidence >= 0.5:
            return (
                "You may consider buying put options, but use caution. "
                "The signals are moderate, so consider smaller position sizes."
            )
        else:
            return (
                "Put options are possible but not strongly recommended. "
                "The signals are weak, and the risk may outweigh potential rewards."
            )
    else:  # No Trade
        return (
            "No action is recommended at this time. "
            "The market conditions are not clear enough to make a confident trading decision. "
            "Sometimes the best trade is no trade."
        )


def _explain_why(
    evaluation: EvaluationResult,
    score_result: ScoreResult | None = None,
) -> List[str]:
    """Generate bullet points explaining why the signal was generated.

    Args:
        evaluation: Evaluation result from rule engine.
        score_result: Optional score result for additional context.

    Returns:
        List of beginner-friendly explanation bullet points.
    """
    reasons = []

    # Add confidence level explanation
    confidence = evaluation.confidence_score
    if confidence >= 0.7:
        reasons.append(
            f"The analysis shows {confidence:.0%} confidence, meaning multiple indicators agree on the direction."
        )
    elif confidence >= 0.5:
        reasons.append(
            f"The analysis shows {confidence:.0%} confidence, with some indicators supporting this view."
        )
    else:
        reasons.append(
            f"The analysis shows {confidence:.0%} confidence, indicating mixed or weak signals."
        )

    # Add rule-based explanations
    for rule_result in evaluation.rule_results:
        if rule_result.triggered and abs(rule_result.signal_strength) > 0.1:
            # Convert technical explanation to beginner-friendly
            explanation = rule_result.explanation

            # Simplify PCR explanations
            if "PCR" in rule_result.name:
                if "high" in explanation.lower() or "above" in explanation.lower():
                    reasons.append(
                        "Put-Call Ratio is elevated, suggesting traders are buying more put protection. "
                        "This often indicates bullish sentiment."
                    )
                elif "low" in explanation.lower() or "below" in explanation.lower():
                    reasons.append(
                        "Put-Call Ratio is low, suggesting traders are buying more call options. "
                        "This often indicates bearish sentiment."
                    )

            # Simplify OI build-up explanations
            elif "OI Build-up" in rule_result.name:
                if "Long" in explanation:
                    reasons.append(
                        "Open Interest is increasing for both calls and puts, suggesting strong "
                        "directional positions are being built."
                    )
                elif "Short" in explanation:
                    reasons.append(
                        "Open Interest is decreasing, suggesting positions are being closed. "
                        "This may indicate uncertainty."
                    )
                elif "Unwinding" in explanation:
                    reasons.append(
                        "Open Interest shows mixed changes, suggesting the market may move sideways."
                    )

            # Simplify Max OI explanations
            elif "Max OI" in rule_result.name:
                if "support" in explanation.lower():
                    reasons.append(
                        "Maximum Put Open Interest is below current price, acting as a support level. "
                        "This suggests the market may find buying interest at lower levels."
                    )
                elif "resistance" in explanation.lower():
                    reasons.append(
                        "Maximum Call Open Interest is above current price, acting as a resistance level. "
                        "This suggests the market may face selling pressure at higher levels."
                    )

            # Simplify Support/Resistance explanations
            elif "Support/Resistance" in rule_result.name:
                if "support" in explanation.lower() and "close" in explanation.lower():
                    reasons.append(
                        "Strong support level is nearby, which may help prevent further price declines."
                    )
                elif "resistance" in explanation.lower() and "close" in explanation.lower():
                    reasons.append(
                        "Strong resistance level is nearby, which may limit further price gains."
                    )

    # Add signal strength context
    signal_strength = abs(evaluation.signal_strength)
    if signal_strength >= 0.6:
        reasons.append("The overall signal strength is strong, with clear directional bias.")
    elif signal_strength >= 0.3:
        reasons.append("The overall signal strength is moderate, showing some directional preference.")

    return reasons


def _explain_risk_level(
    evaluation: EvaluationResult,
    safety: SafetyResult | None = None,
) -> str:
    """Explain risk level in beginner-friendly terms.

    Args:
        evaluation: Evaluation result from rule engine.
        safety: Optional safety result for additional context.

    Returns:
        Beginner-friendly risk level explanation.
    """
    risk_level = evaluation.risk_level

    # Check for safety blocks
    if safety and safety.blocked:
        return (
            "HIGH RISK: Trading is blocked due to safety concerns. "
            "Market conditions are not suitable for beginner traders at this time."
        )

    # Check for risk reasons
    if evaluation.risk_reasons:
        if risk_level == "High":
            return (
                "HIGH RISK: Multiple risk factors are present. "
                "Consider avoiding trades or using very small position sizes with strict stop-losses."
            )
        elif risk_level == "Medium":
            return (
                "MODERATE RISK: Some risk factors are present. "
                "Use caution, smaller position sizes, and always set stop-losses."
            )
    else:
        if risk_level == "High":
            return (
                "HIGH RISK: The analysis indicates elevated risk levels. "
                "Proceed with extreme caution and consider waiting for better conditions."
            )
        elif risk_level == "Medium":
            return (
                "MODERATE RISK: Standard options trading risks apply. "
                "Use proper position sizing and risk management."
            )
        else:  # Low
            return (
                "LOW RISK: Relative to options trading, risk levels appear manageable. "
                "However, remember that all options trading carries risk of total loss."
            )

    return "Risk assessment is unavailable. Always use caution when trading options."


def _explain_what_can_go_wrong(
    evaluation: EvaluationResult,
    safety: SafetyResult | None = None,
) -> List[str]:
    """Explain potential risks in beginner-friendly terms.

    Args:
        evaluation: Evaluation result from rule engine.
        safety: Optional safety result for additional context.

    Returns:
        List of beginner-friendly risk explanations.
    """
    risks = []

    # Always include basic options risks
    risks.append(
        "Options can expire worthless: If the market doesn't move in your favor before expiry, "
        "you may lose your entire investment."
    )

    risks.append(
        "Time decay: Even if the market moves in your direction, time decay can erode option value. "
        "Options lose value as they approach expiration."
    )

    # Add confidence-based risks
    confidence = evaluation.confidence_score
    if confidence < 0.5:
        risks.append(
            "Low confidence signal: The analysis shows weak signals, meaning the market direction "
            "is uncertain. The trade may not work out as expected."
        )

    # Add risk level specific warnings
    if evaluation.risk_level == "High":
        risks.append(
            "High risk conditions: Multiple risk factors are present, increasing the chance of losses. "
            "Consider avoiding trades or using very small positions."
        )

    # Add specific risk reasons
    for risk_reason in evaluation.risk_reasons:
        if "extreme" in risk_reason.lower():
            risks.append(
                "Extreme market conditions detected: The market may be overextended and could reverse "
                "unexpectedly, causing losses."
            )
        elif "missing" in risk_reason.lower():
            risks.append(
                "Incomplete data: Some analysis data is missing, which means the signal may be less reliable."
            )

    # Add safety warnings
    if safety:
        for warning in safety.warnings:
            if "🚫" in warning or "BLOCKED" in warning.upper():
                # Extract the key message
                if "WEEKLY EXPIRY" in warning.upper():
                    risks.append(
                        "Weekly expiry risk: Options expiring soon have very high time decay. "
                        "You may lose money even if the market moves in your favor."
                    )
                elif "LOW IV" in warning.upper() or "VERY LOW IV" in warning.upper():
                    risks.append(
                        "Low volatility risk: When volatility is low, option premiums are smaller. "
                        "This means you need larger price moves to profit, and losses can be significant."
                    )

        if "FAR OTM" in " ".join(safety.warnings).upper():
            risks.append(
                "Far out-of-the-money risk: Options far from current price have lower probability "
                "of becoming profitable. Most such options expire worthless."
            )

    # Add trade-specific risks
    if evaluation.trade_recommendation == "Call":
        risks.append(
            "Call option risk: If the market doesn't rise enough, or falls, your call options will lose value. "
            "You need the market to move up significantly to profit."
        )
    elif evaluation.trade_recommendation == "Put":
        risks.append(
            "Put option risk: If the market doesn't fall enough, or rises, your put options will lose value. "
            "You need the market to move down significantly to profit."
        )

    return risks


def explain(
    evaluation: EvaluationResult,
    score_result: ScoreResult | None = None,
    safety: SafetyResult | None = None,
) -> Explanation:
    """Convert technical signals into beginner-friendly explanations.

    Takes technical analysis outputs and converts them into clear, educational,
    and calm explanations suitable for beginners.

    Args:
        evaluation: Evaluation result from rule engine.
        score_result: Optional score result for additional context.
        safety: Optional safety result for risk warnings.

    Returns:
        Explanation with:
            - market_bias: Clear explanation of market direction
            - suggested_action: What to do (or not do)
            - why: Bullet points explaining the reasoning
            - risk_level: Risk assessment in plain language
            - what_can_go_wrong: List of potential risks explained simply
    """
    return Explanation(
        market_bias=_explain_market_bias(evaluation, score_result),
        suggested_action=_explain_suggested_action(evaluation, safety),
        why=_explain_why(evaluation, score_result),
        risk_level=_explain_risk_level(evaluation, safety),
        what_can_go_wrong=_explain_what_can_go_wrong(evaluation, safety),
    )
