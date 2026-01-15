"""Streamlit UI for NIFTY Options AI Assistant."""

from __future__ import annotations

import time
from datetime import datetime

import pandas as pd
import streamlit as st

from core.converter import convert_to_dataframe
from core.features import calculate_features
from core.nse_option_chain import NSEDataFetchError, fetch_nifty_option_chain
from core.validator import ValidationError, validate_nifty_option_chain
from rules import (
    calculate_score,
    check_safety,
    evaluate,
    explain,
)


# Page configuration
st.set_page_config(
    page_title="NIFTY Options AI Assistant",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for professional look
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #1f77b4;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffc107;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .blocking-box {
        background-color: #f8d7da;
        border: 1px solid #dc3545;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #28a745;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #17a2b8;
        border-radius: 0.5rem;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def format_percentage(value: float | None) -> str:
    """Format value as percentage."""
    if value is None:
        return "N/A"
    return f"{value:.1%}"


def format_number(value: float | None, decimals: int = 0) -> str:
    """Format number with commas."""
    if value is None:
        return "N/A"
    return f"{value:,.{decimals}f}"


def get_bias_color(bias: str) -> str:
    """Get color for market bias."""
    if bias == "Bullish":
        return "#28a745"
    elif bias == "Bearish":
        return "#dc3545"
    elif bias == "Sideways":
        return "#ffc107"
    else:
        return "#6c757d"


def get_risk_color(risk_level: str) -> str:
    """Get color for risk level."""
    if risk_level == "Low":
        return "#28a745"
    elif risk_level == "Medium":
        return "#ffc107"
    else:
        return "#dc3545"


@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_and_analyze():
    """Fetch and analyze NIFTY options data."""
    try:
        # Fetch data
        raw_data = fetch_nifty_option_chain()

        # Validate
        validated_data = validate_nifty_option_chain(raw_data)

        # Convert to DataFrame
        df = convert_to_dataframe(validated_data)

        if df.empty:
            return None, "No data available"

        # Calculate features
        features = calculate_features(df, raw_data=validated_data)

        # Evaluate rules
        evaluation = evaluate(features)

        # Calculate score
        score_result = calculate_score(evaluation.rule_results)

        # Check safety
        safety = check_safety(df, raw_data=validated_data, features=features)

        # Generate explanation
        explanation = explain(evaluation, score_result, safety)

        return {
            "df": df,
            "features": features,
            "evaluation": evaluation,
            "score_result": score_result,
            "safety": safety,
            "explanation": explanation,
            "raw_data": validated_data,
        }, None

    except NSEDataFetchError as e:
        return None, f"Failed to fetch data: {str(e)}"
    except ValidationError as e:
        return None, f"Data validation error: {str(e)}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def main():
    """Main Streamlit app."""
    # Header
    st.markdown('<h1 class="main-header">📊 NIFTY Options AI Assistant</h1>', unsafe_allow_html=True)

    # Sidebar
    with st.sidebar:
        st.header("Settings")
        block_weekly = st.checkbox("Block Weekly Expiry", value=True, help="Block options expiring within 7 days")
        auto_refresh = st.checkbox("Auto Refresh (60s)", value=False)

        st.markdown("---")
        st.markdown("### About")
        st.markdown(
            """
            This tool analyzes NIFTY 50 options data and provides
            AI-powered trading signals with risk assessment.
            
            **For educational purposes only.**
            """
        )

    # Refresh button
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🔄 Refresh Data", type="primary"):
            st.cache_data.clear()
            st.rerun()

    with col2:
        st.caption(f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Fetch and analyze data
    with st.spinner("Fetching live data and analyzing..."):
        result, error = fetch_and_analyze()

    if error:
        st.error(f"❌ {error}")
        
        # Provide helpful guidance based on error type
        if "403" in error or "Forbidden" in error:
            st.warning("""
            **403 Forbidden Error - Common Causes:**
            
            1. **Market is closed**: NSE trading hours are 9:15 AM - 3:30 PM IST (Mon-Fri)
            2. **Rate limiting**: Too many requests. Wait 10-15 minutes and try again.
            3. **Anti-scraping**: NSE detected automated access.
            
            **Solutions:**
            - Try during market hours for best results
            - Wait 10-15 minutes before retrying
            - Click the refresh button to try again
            """)
        else:
            st.info("Please try again in a few moments or check your internet connection.")
        return

    if result is None:
        st.warning("No data available. Please try again later.")
        return

    # Extract results
    features = result["features"]
    evaluation = result["evaluation"]
    score_result = result["score_result"]
    safety = result["safety"]
    explanation = result["explanation"]

    # Key Metrics Section
    st.markdown("---")
    st.header("📈 Key Metrics")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        underlying = features.get("underlying_value")
        st.metric("Underlying Price", format_number(underlying, 2) if underlying else "N/A")

    with col2:
        atm_strike = features.get("atm_strike")
        st.metric("ATM Strike", format_number(atm_strike, 0) if atm_strike else "N/A")

    with col3:
        pcr = features.get("overall_pcr")
        st.metric("Put-Call Ratio", f"{pcr:.2f}" if pcr else "N/A")

    with col4:
        oi_type = features.get("oi_buildup_type", "Unknown")
        st.metric("OI Build-up", oi_type)

    # Additional metrics row
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        max_call_oi = features.get("max_call_oi_strike")
        st.metric("Max Call OI Strike", format_number(max_call_oi, 0) if max_call_oi else "N/A")

    with col2:
        max_put_oi = features.get("max_put_oi_strike")
        st.metric("Max Put OI Strike", format_number(max_put_oi, 0) if max_put_oi else "N/A")

    with col3:
        support = features.get("support")
        st.metric("Support Level", format_number(support, 0) if support else "N/A")

    with col4:
        resistance = features.get("resistance")
        st.metric("Resistance Level", format_number(resistance, 0) if resistance else "N/A")

    # AI Recommendation Section
    st.markdown("---")
    st.header("🤖 AI Recommendation")

    # Main recommendation card
    bias_color = get_bias_color(evaluation.market_bias)
    risk_color = get_risk_color(evaluation.risk_level)

    rec_col1, rec_col2, rec_col3 = st.columns([2, 1, 1])

    with rec_col1:
        st.markdown(f"### Market Bias: <span style='color: {bias_color}'>{evaluation.market_bias}</span>", unsafe_allow_html=True)
        st.markdown(f"**Suggested Action:** {explanation.suggested_action}")

    with rec_col2:
        score = score_result.final_score
        score_color = "#28a745" if score > 0.3 else "#dc3545" if score < -0.3 else "#ffc107"
        st.metric("Signal Score", f"{score:.2f}", delta=score_result.category)
        st.caption(f"Category: {score_result.category}")

    with rec_col3:
        confidence = evaluation.confidence_score
        st.metric("Confidence", format_percentage(confidence))
        st.metric("Risk Level", evaluation.risk_level)

    # Recommendation details
    st.markdown("#### Why:")
    for reason in explanation.why:
        st.markdown(f"• {reason}")

    # Risk Warnings Section
    st.markdown("---")
    st.header("⚠️ Risk Warnings")

    # Check if blocked
    if safety.blocked:
        st.markdown(
            f'<div class="blocking-box">'
            f'<strong>🚫 Trading Blocked</strong><br>'
            f'{safety.block_reason or "Safety checks have identified conditions not suitable for beginners."}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # Display warnings
    blocking_warnings = []
    regular_warnings = []
    info_warnings = []

    for warning in safety.warnings:
        if "🚫" in warning or "BLOCKED" in warning.upper():
            blocking_warnings.append(warning)
        elif "⚠️" in warning:
            regular_warnings.append(warning)
        else:
            info_warnings.append(warning)

    # Add evaluation risk reasons
    for risk_reason in evaluation.risk_reasons:
        regular_warnings.append(risk_reason)

    # Display blocking warnings
    for warning in blocking_warnings:
        clean_warning = warning.replace("🚫", "").strip()
        st.markdown(
            f'<div class="blocking-box"><strong>🚫 Blocking Warning:</strong><br>{clean_warning}</div>',
            unsafe_allow_html=True,
        )

    # Display regular warnings
    for warning in regular_warnings:
        clean_warning = warning.replace("⚠️", "").strip()
        st.markdown(
            f'<div class="warning-box"><strong>⚠️ Warning:</strong><br>{clean_warning}</div>',
            unsafe_allow_html=True,
        )

    # Display info warnings
    for warning in info_warnings:
        st.markdown(
            f'<div class="info-box"><strong>ℹ️ Info:</strong><br>{warning}</div>',
            unsafe_allow_html=True,
        )

    # What Can Go Wrong Section
    st.markdown("---")
    st.header("⚠️ What Can Go Wrong")

    for risk in explanation.what_can_go_wrong:
        st.markdown(f"• {risk}")

    # Risk Level Details
    st.markdown("---")
    st.markdown(f"#### Risk Assessment: <span style='color: {risk_color}'>{evaluation.risk_level} Risk</span>", unsafe_allow_html=True)
    st.markdown(explanation.risk_level)

    # Footer
    st.markdown("---")
    st.markdown(
        """
        <div style='text-align: center; color: #6c757d; padding: 1rem;'>
        <small>
        ⚠️ <strong>Disclaimer:</strong> This tool is for educational purposes only. 
        Options trading involves significant risk. Past performance does not guarantee future results. 
        Consult a financial advisor before making investment decisions.
        </small>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Auto-refresh
    if auto_refresh:
        time.sleep(60)
        st.rerun()


if __name__ == "__main__":
    main()
