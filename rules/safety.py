"""Safety layer for beginner-friendly option trading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List

import pandas as pd


@dataclass
class SafetyResult:
    """Result from safety checks."""

    is_safe: bool  # Whether trading is safe for beginners
    warnings: List[str]  # List of safety warnings
    blocked: bool  # Whether trading should be blocked
    block_reason: str | None  # Reason if blocked


# Safety thresholds
_SAFETY_THRESHOLDS = {
    "weekly_expiry_days": 7,  # Block expiries within 7 days
    "far_otm_percentage": 5.0,  # Block strikes >5% away from ATM
    "low_iv_threshold": 15.0,  # Warn if IV < 15%
    "very_low_iv_threshold": 10.0,  # Block if IV < 10%
}

# Capital risk disclaimer (always included)
_CAPITAL_RISK_DISCLAIMER = (
    "⚠️ CAPITAL RISK DISCLAIMER: Options trading involves significant risk. "
    "You may lose your entire investment. Only trade with capital you can afford to lose. "
    "Past performance does not guarantee future results. Consult a financial advisor if needed."
)


def _extract_expiry_dates(raw_data: Dict[str, Any]) -> List[str]:
    """Extract expiry dates from raw NSE data.

    Args:
        raw_data: Raw JSON dictionary from NSE API.

    Returns:
        List of expiry date strings.
    """
    expiry_dates = []

    # Try to get from records.expiryDates
    if "records" in raw_data and isinstance(raw_data["records"], dict):
        expiry_dates_list = raw_data["records"].get("expiryDates", [])
        if isinstance(expiry_dates_list, list):
            expiry_dates.extend(expiry_dates_list)

    # Try to get from filtered.expiryDates
    if "filtered" in raw_data and isinstance(raw_data["filtered"], dict):
        expiry_dates_list = raw_data["filtered"].get("expiryDates", [])
        if isinstance(expiry_dates_list, list):
            expiry_dates.extend(expiry_dates_list)

    # Extract unique expiry dates from option data
    if "records" in raw_data and isinstance(raw_data["records"], dict):
        records_data = raw_data["records"].get("data", [])
        if isinstance(records_data, list):
            for record in records_data:
                if isinstance(record, dict):
                    for option_type in ["CE", "PE"]:
                        option_data = record.get(option_type)
                        if option_data and isinstance(option_data, dict):
                            expiry = option_data.get("expiryDate")
                            if expiry and expiry not in expiry_dates:
                                expiry_dates.append(expiry)

    return list(set(expiry_dates))  # Remove duplicates


def _parse_expiry_date(expiry_str: str) -> datetime | None:
    """Parse expiry date string to datetime.

    Args:
        expiry_str: Expiry date string (e.g., "25-Jan-2024").

    Returns:
        Datetime object or None if parsing fails.
    """
    if not expiry_str:
        return None

    # Common NSE date formats
    formats = [
        "%d-%b-%Y",  # 25-Jan-2024
        "%d-%m-%Y",  # 25-01-2024
        "%Y-%m-%d",  # 2024-01-25
        "%d/%m/%Y",  # 25/01/2024
    ]

    for fmt in formats:
        try:
            return datetime.strptime(expiry_str, fmt)
        except (ValueError, TypeError):
            continue

    return None


def _is_weekly_expiry(expiry_date: datetime, current_date: datetime | None = None) -> bool:
    """Check if expiry is within weekly threshold.

    Args:
        expiry_date: Expiry date to check.
        current_date: Current date (defaults to now).

    Returns:
        True if expiry is within weekly threshold.
    """
    if current_date is None:
        current_date = datetime.now()

    days_until_expiry = (expiry_date - current_date).days
    return 0 <= days_until_expiry <= _SAFETY_THRESHOLDS["weekly_expiry_days"]


def _check_weekly_expiry(raw_data: Dict[str, Any]) -> tuple[bool, List[str]]:
    """Check for weekly expiry options.

    Args:
        raw_data: Raw JSON dictionary from NSE API.

    Returns:
        Tuple of (has_weekly_expiry, warnings).
    """
    warnings = []
    expiry_dates = _extract_expiry_dates(raw_data)

    if not expiry_dates:
        warnings.append("⚠️ Unable to determine expiry dates. Exercise caution with expiry selection.")
        return False, warnings

    current_date = datetime.now()
    weekly_expiries = []

    for expiry_str in expiry_dates:
        expiry_date = _parse_expiry_date(expiry_str)
        if expiry_date and _is_weekly_expiry(expiry_date, current_date):
            weekly_expiries.append(expiry_str)

    if weekly_expiries:
        warnings.append(
            f"🚫 WEEKLY EXPIRY DETECTED: Options expiring within {_SAFETY_THRESHOLDS['weekly_expiry_days']} days "
            f"({', '.join(weekly_expiries)}). Weekly expiries are blocked for beginners due to high time decay risk."
        )
        return True, warnings

    return False, warnings


def _check_far_otm(
    df: pd.DataFrame,
    underlying_value: float | None,
    atm_strike: float | None,
) -> List[str]:
    """Check for far OTM (Out of The Money) options.

    Args:
        df: DataFrame with strike prices.
        underlying_value: Current underlying price.
        atm_strike: ATM strike price.

    Returns:
        List of warnings.
    """
    warnings = []

    if df.empty or "strike_price" not in df.columns:
        return warnings

    if underlying_value is None and atm_strike is None:
        warnings.append("⚠️ Unable to determine ATM strike. Cannot check for far OTM options.")
        return warnings

    reference_price = underlying_value if underlying_value is not None else atm_strike
    if reference_price is None:
        return warnings

    # Calculate OTM percentage for each strike
    df_clean = df.dropna(subset=["strike_price"])
    if df_clean.empty:
        return warnings

    otm_threshold = _SAFETY_THRESHOLDS["far_otm_percentage"]
    far_otm_strikes = []

    for _, row in df_clean.iterrows():
        strike = row["strike_price"]
        otm_pct = abs((strike - reference_price) / reference_price) * 100

        if otm_pct > otm_threshold:
            far_otm_strikes.append((strike, otm_pct))

    if far_otm_strikes:
        # Get the furthest OTM strike as example
        max_otm = max(far_otm_strikes, key=lambda x: x[1])
        warnings.append(
            f"⚠️ FAR OTM OPTIONS DETECTED: Some strikes are >{otm_threshold}% away from ATM "
            f"(e.g., {max_otm[0]:.0f} is {max_otm[1]:.1f}% OTM). "
            f"Far OTM options have lower probability of profit and higher risk."
        )

    return warnings


def _check_iv_levels(df: pd.DataFrame) -> List[str]:
    """Check for low or falling IV.

    Args:
        df: DataFrame with IV columns.

    Returns:
        List of warnings.
    """
    warnings = []

    if df.empty:
        return warnings

    # Check call IV
    call_iv_col = "call_iv"
    put_iv_col = "put_iv"

    iv_values = []
    if call_iv_col in df.columns:
        call_iv = df[call_iv_col].dropna()
        iv_values.extend(call_iv.tolist())

    if put_iv_col in df.columns:
        put_iv = df[put_iv_col].dropna()
        iv_values.extend(put_iv.tolist())

    if not iv_values:
        warnings.append("⚠️ IV data not available. Cannot assess volatility risk.")
        return warnings

    # Calculate average IV
    avg_iv = sum(iv_values) / len(iv_values) if iv_values else 0.0
    min_iv = min(iv_values) if iv_values else 0.0

    # Check for very low IV (blocking condition)
    if min_iv < _SAFETY_THRESHOLDS["very_low_iv_threshold"]:
        warnings.append(
            f"🚫 VERY LOW IV DETECTED: Minimum IV is {min_iv:.1f}% (below {_SAFETY_THRESHOLDS['very_low_iv_threshold']}%). "
            f"Very low IV makes options less profitable and increases risk. Trading is blocked."
        )
    # Check for low IV (warning)
    elif avg_iv < _SAFETY_THRESHOLDS["low_iv_threshold"]:
        warnings.append(
            f"⚠️ LOW IV WARNING: Average IV is {avg_iv:.1f}% (below {_SAFETY_THRESHOLDS['low_iv_threshold']}%). "
            f"Low IV reduces option premiums and profit potential. Consider waiting for higher volatility."
        )

    # Check for falling IV trend (if we have historical data, this would be more accurate)
    # For now, we'll note if IV is consistently low
    if avg_iv < _SAFETY_THRESHOLDS["low_iv_threshold"]:
        warnings.append(
            "⚠️ FALLING IV RISK: Low IV suggests decreasing volatility. "
            "Options may lose value faster due to volatility crush."
        )

    return warnings


def check_safety(
    df: pd.DataFrame,
    raw_data: Dict[str, Any] | None = None,
    features: Dict[str, Any] | None = None,
    block_weekly_expiry: bool = True,
) -> SafetyResult:
    """Perform safety checks for beginner-friendly option trading.

    Args:
        df: DataFrame from convert_to_dataframe() with option chain data.
        raw_data: Optional raw JSON data for expiry date extraction.
        features: Optional features dictionary for underlying/ATM values.
        block_weekly_expiry: Whether to block weekly expiry (default: True).

    Returns:
        SafetyResult with safety status, warnings, and block status.
    """
    warnings: List[str] = []
    blocked = False
    block_reason: str | None = None

    # Always include capital risk disclaimer
    warnings.append(_CAPITAL_RISK_DISCLAIMER)

    # Check weekly expiry
    if block_weekly_expiry and raw_data is not None:
        has_weekly, weekly_warnings = _check_weekly_expiry(raw_data)
        warnings.extend(weekly_warnings)
        if has_weekly:
            blocked = True
            block_reason = "Weekly expiry detected (blocked for beginners)"

    # Check far OTM options
    underlying_value = None
    atm_strike = None
    if features:
        underlying_value = features.get("underlying_value")
        atm_strike = features.get("atm_strike")

    otm_warnings = _check_far_otm(df, underlying_value, atm_strike)
    warnings.extend(otm_warnings)

    # Check IV levels
    iv_warnings = _check_iv_levels(df)
    warnings.extend(iv_warnings)

    # Check if any blocking conditions are met
    for warning in iv_warnings:
        if "🚫" in warning or "VERY LOW IV" in warning:
            blocked = True
            if block_reason is None:
                block_reason = "Very low IV detected"

    # Determine overall safety
    is_safe = not blocked and len([w for w in warnings if "🚫" in w]) == 0

    return SafetyResult(
        is_safe=is_safe,
        warnings=warnings,
        blocked=blocked,
        block_reason=block_reason,
    )
