"""FastAPI application for NIFTY options analysis."""

from __future__ import annotations

from typing import List

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from core.converter import convert_to_dataframe
from core.features import calculate_features
from core.nse_option_chain import NSEDataFetchError, fetch_nifty_option_chain
from core.validator import ValidationError, validate_nifty_option_chain
from rules import (
    EvaluationResult,
    Explanation,
    SafetyResult,
    ScoreResult,
    calculate_score,
    check_safety,
    evaluate,
    explain,
)

app = FastAPI(
    title="NIFTY Options AI Assistant",
    description="AI-powered analysis for NIFTY 50 options trading",
    version="1.0.0",
)


class AnalysisRequest(BaseModel):
    """Request model for options analysis."""

    block_weekly_expiry: bool = Field(
        default=True,
        description="Block weekly expiry options (default: True for beginners)",
    )


class WarningItem(BaseModel):
    """Individual warning item."""

    message: str = Field(..., description="Warning message")
    severity: str = Field(..., description="Warning severity: 'blocking', 'warning', or 'info'")


class WhyItem(BaseModel):
    """Individual 'why' explanation item."""

    reason: str = Field(..., description="Explanation reason")


class RiskItem(BaseModel):
    """Individual risk item."""

    risk: str = Field(..., description="Risk description")


class AnalysisResponse(BaseModel):
    """Response model for options analysis."""

    bias: str = Field(..., description="Market bias: Bullish, Bearish, Sideways, or No-Trade")
    score: float = Field(..., description="Final score between -1.0 and +1.0")
    score_category: str = Field(
        ...,
        description="Score category: Strong Bullish, Mild Bullish, Neutral, Mild Bearish, or Strong Bearish",
    )
    recommendation: str = Field(..., description="Trade recommendation: Call, Put, or No Trade")
    confidence_score: float = Field(..., description="Confidence score between 0.0 and 1.0")
    risk_level: str = Field(..., description="Risk level: Low, Medium, or High")
    explanation: ExplanationDetail = Field(..., description="Beginner-friendly explanation")
    warnings: List[WarningItem] = Field(..., description="List of warnings and safety alerts")


class ExplanationDetail(BaseModel):
    """Detailed explanation structure."""

    market_bias: str = Field(..., description="Market bias explanation")
    suggested_action: str = Field(..., description="Suggested trading action")
    why: List[WhyItem] = Field(..., description="List of reasons explaining the analysis")
    risk_level_description: str = Field(..., description="Risk level explanation")
    what_can_go_wrong: List[RiskItem] = Field(..., description="List of potential risks")


def _convert_explanation_to_response(explanation: Explanation) -> ExplanationDetail:
    """Convert Explanation to ExplanationDetail response model."""
    return ExplanationDetail(
        market_bias=explanation.market_bias,
        suggested_action=explanation.suggested_action,
        why=[WhyItem(reason=reason) for reason in explanation.why],
        risk_level_description=explanation.risk_level,
        what_can_go_wrong=[RiskItem(risk=risk) for risk in explanation.what_can_go_wrong],
    )


def _convert_warnings_to_response(
    safety: SafetyResult,
    evaluation: EvaluationResult,
) -> List[WarningItem]:
    """Convert safety and evaluation warnings to response format."""
    warnings = []

    # Add safety warnings
    for warning in safety.warnings:
        if "🚫" in warning or "BLOCKED" in warning.upper():
            severity = "blocking"
        elif "⚠️" in warning:
            severity = "warning"
        else:
            severity = "info"

        # Clean up emoji for API response
        clean_warning = warning.replace("🚫", "").replace("⚠️", "").strip()
        warnings.append(WarningItem(message=clean_warning, severity=severity))

    # Add evaluation risk reasons
    for risk_reason in evaluation.risk_reasons:
        warnings.append(WarningItem(message=risk_reason, severity="warning"))

    return warnings


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NIFTY Options AI Assistant API",
        "version": "1.0.0",
        "endpoints": {
            "analyze": "/analyze/nifty-options",
        },
    }


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/analyze/nifty-options", response_model=AnalysisResponse)
async def analyze_nifty_options(request: AnalysisRequest = AnalysisRequest()):
    """Analyze NIFTY 50 options and provide trading signals.

    This endpoint:
    1. Fetches current NIFTY option chain data from NSE
    2. Validates and processes the data
    3. Calculates technical features
    4. Evaluates trading rules
    5. Performs safety checks
    6. Generates beginner-friendly explanations

    Args:
        request: Analysis request with optional parameters.

    Returns:
        AnalysisResponse with bias, score, recommendation, explanation, and warnings.

    Raises:
        HTTPException: If data fetching, validation, or processing fails.
    """
    try:
        # Step 1: Fetch raw data from NSE
        raw_data = fetch_nifty_option_chain()

        # Step 2: Validate data
        validated_data = validate_nifty_option_chain(raw_data)

        # Step 3: Convert to DataFrame
        df = convert_to_dataframe(validated_data)

        if df.empty:
            raise HTTPException(
                status_code=503,
                detail="No option chain data available. Please try again later.",
            )

        # Step 4: Calculate features
        features = calculate_features(df, raw_data=validated_data)

        # Step 5: Evaluate rules
        evaluation = evaluate(features)

        # Step 6: Calculate score
        score_result = calculate_score(evaluation.rule_results)

        # Step 7: Check safety
        safety = check_safety(
            df,
            raw_data=validated_data,
            features=features,
            block_weekly_expiry=request.block_weekly_expiry,
        )

        # Step 8: Generate explanation
        explanation = explain(evaluation, score_result, safety)

        # Step 9: Convert to response format
        explanation_detail = _convert_explanation_to_response(explanation)
        warnings = _convert_warnings_to_response(safety, evaluation)

        # Build response
        return AnalysisResponse(
            bias=evaluation.market_bias,
            score=score_result.final_score,
            score_category=score_result.category,
            recommendation=evaluation.trade_recommendation,
            confidence_score=evaluation.confidence_score,
            risk_level=evaluation.risk_level,
            explanation=explanation_detail,
            warnings=warnings,
        )

    except NSEDataFetchError as e:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to fetch data from NSE: {str(e)}",
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=422,
            detail=f"Data validation failed: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
        )
