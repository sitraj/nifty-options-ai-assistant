"""Feature engineering module for NSE option chain analysis."""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd


def _get_underlying_value(data: Dict[str, Any]) -> float | None:
    """Extract underlying value from raw NSE data.

    Args:
        data: Raw JSON dictionary from NSE API.

    Returns:
        Underlying value (spot price) or None if not found.
    """
    # Try to get from records.underlyingValue
    if "records" in data and isinstance(data["records"], dict):
        underlying = data["records"].get("underlyingValue")
        if underlying is not None:
            try:
                return float(underlying)
            except (ValueError, TypeError):
                pass

    # Try to get from filtered.underlyingValue
    if "filtered" in data and isinstance(data["filtered"], dict):
        underlying = data["filtered"].get("underlyingValue")
        if underlying is not None:
            try:
                return float(underlying)
            except (ValueError, TypeError):
                pass

    # Try to get from first record's CE or PE
    if "records" in data and isinstance(data["records"], dict):
        records_data = data["records"].get("data", [])
        if records_data and isinstance(records_data, list) and len(records_data) > 0:
            first_record = records_data[0]
            if isinstance(first_record, dict):
                for option_type in ["CE", "PE"]:
                    option_data = first_record.get(option_type)
                    if option_data and isinstance(option_data, dict):
                        underlying = option_data.get("underlyingValue")
                        if underlying is not None:
                            try:
                                return float(underlying)
                            except (ValueError, TypeError):
                                pass

    return None


def _calculate_atm_strike(
    df: pd.DataFrame,
    underlying_value: float | None,
) -> float | None:
    """Calculate At The Money (ATM) strike price.

    Args:
        df: DataFrame with strike_price column.
        underlying_value: Current underlying/spot price.

    Returns:
        ATM strike price (closest to underlying) or None.
    """
    if df.empty or underlying_value is None:
        return None

    if "strike_price" not in df.columns:
        return None

    # Find strike closest to underlying value
    df_clean = df.dropna(subset=["strike_price"])
    if df_clean.empty:
        return None

    df_clean = df_clean.copy()
    df_clean["distance"] = abs(df_clean["strike_price"] - underlying_value)
    atm_row = df_clean.loc[df_clean["distance"].idxmin()]

    return float(atm_row["strike_price"])


def _calculate_overall_pcr(df: pd.DataFrame) -> float | None:
    """Calculate overall Put-Call Ratio.

    Args:
        df: DataFrame with call_oi and put_oi columns.

    Returns:
        Overall PCR (total put OI / total call OI) or None.
    """
    if df.empty:
        return None

    # Sum all call and put OI
    total_call_oi = df["call_oi"].fillna(0).sum()
    total_put_oi = df["put_oi"].fillna(0).sum()

    if total_call_oi == 0:
        return None

    return float(total_put_oi / total_call_oi)


def _calculate_strike_wise_pcr(df: pd.DataFrame) -> pd.Series:
    """Calculate Put-Call Ratio for each strike price.

    Args:
        df: DataFrame with strike_price, call_oi, and put_oi columns.

    Returns:
        Series with strike_price as index and PCR as values.
    """
    if df.empty or "strike_price" not in df.columns:
        return pd.Series(dtype=float)

    df_clean = df.copy()
    df_clean["call_oi"] = df_clean["call_oi"].fillna(0)
    df_clean["put_oi"] = df_clean["put_oi"].fillna(0)

    # Calculate PCR for each strike
    pcr = df_clean.apply(
        lambda row: (
            row["put_oi"] / row["call_oi"]
            if row["call_oi"] > 0
            else None
        ),
        axis=1,
    )

    result = pd.Series(pcr.values, index=df_clean["strike_price"].values)
    return result


def _calculate_max_oi_strikes(df: pd.DataFrame) -> Dict[str, float | None]:
    """Calculate strikes with maximum Call and Put OI.

    Args:
        df: DataFrame with strike_price, call_oi, and put_oi columns.

    Returns:
        Dictionary with max_call_oi_strike and max_put_oi_strike.
    """
    result = {
        "max_call_oi_strike": None,
        "max_put_oi_strike": None,
    }

    if df.empty or "strike_price" not in df.columns:
        return result

    df_clean = df.copy()

    # Max Call OI strike
    if "call_oi" in df_clean.columns:
        call_oi_clean = df_clean["call_oi"].fillna(0)
        if call_oi_clean.max() > 0:
            max_call_idx = call_oi_clean.idxmax()
            result["max_call_oi_strike"] = float(df_clean.loc[max_call_idx, "strike_price"])

    # Max Put OI strike
    if "put_oi" in df_clean.columns:
        put_oi_clean = df_clean["put_oi"].fillna(0)
        if put_oi_clean.max() > 0:
            max_put_idx = put_oi_clean.idxmax()
            result["max_put_oi_strike"] = float(df_clean.loc[max_put_idx, "strike_price"])

    return result


def _calculate_support_resistance(
    df: pd.DataFrame,
    underlying_value: float | None,
) -> Dict[str, float | None]:
    """Calculate support and resistance levels based on OI concentrations.

    Args:
        df: DataFrame with strike_price, call_oi, and put_oi columns.
        underlying_value: Current underlying/spot price.

    Returns:
        Dictionary with support and resistance levels.
    """
    result = {
        "support": None,
        "resistance": None,
    }

    if df.empty or underlying_value is None:
        return result

    if "strike_price" not in df.columns:
        return result

    df_clean = df.copy()
    df_clean = df_clean.dropna(subset=["strike_price"])

    # Calculate combined OI (put OI for support, call OI for resistance)
    df_clean["put_oi"] = df_clean["put_oi"].fillna(0)
    df_clean["call_oi"] = df_clean["call_oi"].fillna(0)

    # Support: Strike below underlying with max put OI
    below_underlying = df_clean[df_clean["strike_price"] < underlying_value]
    if not below_underlying.empty:
        max_put_idx = below_underlying["put_oi"].idxmax()
        if below_underlying.loc[max_put_idx, "put_oi"] > 0:
            result["support"] = float(below_underlying.loc[max_put_idx, "strike_price"])

    # Resistance: Strike above underlying with max call OI
    above_underlying = df_clean[df_clean["strike_price"] > underlying_value]
    if not above_underlying.empty:
        max_call_idx = above_underlying["call_oi"].idxmax()
        if above_underlying.loc[max_call_idx, "call_oi"] > 0:
            result["resistance"] = float(above_underlying.loc[max_call_idx, "strike_price"])

    return result


def _determine_oi_buildup_type(df: pd.DataFrame) -> str:
    """Determine OI build-up type based on OI changes.

    Args:
        df: DataFrame with call_oi_change and put_oi_change columns.

    Returns:
        OI build-up type: "Long", "Short", "Unwinding", or "Mixed".
    """
    if df.empty:
        return "Unknown"

    df_clean = df.copy()

    # Fill NaN with 0 for calculation
    call_oi_change = df_clean["call_oi_change"].fillna(0)
    put_oi_change = df_clean["put_oi_change"].fillna(0)

    # Calculate total changes
    total_call_change = call_oi_change.sum()
    total_put_change = put_oi_change.sum()

    # Determine build-up type
    # Long: Both call and put OI increasing (bullish/bearish positions)
    # Short: Both call and put OI decreasing (covering positions)
    # Unwinding: One increasing, one decreasing (position unwinding)
    # Mixed: Inconsistent pattern

    if total_call_change > 0 and total_put_change > 0:
        return "Long"
    elif total_call_change < 0 and total_put_change < 0:
        return "Short"
    elif (total_call_change > 0 and total_put_change < 0) or (
        total_call_change < 0 and total_put_change > 0
    ):
        return "Unwinding"
    else:
        return "Mixed"


def calculate_features(
    df: pd.DataFrame,
    raw_data: Dict[str, Any] | None = None,
) -> Dict[str, Any]:
    """Calculate feature engineering metrics from option chain DataFrame.

    Args:
        df: DataFrame from convert_to_dataframe() with option chain data.
        raw_data: Optional raw JSON data to extract underlying value.

    Returns:
        Dictionary containing:
        - atm_strike: At The Money strike price
        - overall_pcr: Overall Put-Call Ratio
        - strike_wise_pcr: Dictionary mapping strike prices to PCR values
        - max_call_oi_strike: Strike with maximum call OI
        - max_put_oi_strike: Strike with maximum put OI
        - support: Support level based on put OI
        - resistance: Resistance level based on call OI
        - oi_buildup_type: OI build-up type (Long/Short/Unwinding/Mixed)
        - underlying_value: Current underlying/spot price (if available)
    """
    if not isinstance(df, pd.DataFrame):
        raise ValueError("df must be a pandas DataFrame")

    # Get underlying value
    underlying_value = None
    if raw_data is not None:
        underlying_value = _get_underlying_value(raw_data)

    # Calculate all metrics
    atm_strike = _calculate_atm_strike(df, underlying_value)
    overall_pcr = _calculate_overall_pcr(df)
    strike_wise_pcr = _calculate_strike_wise_pcr(df)
    max_oi_strikes = _calculate_max_oi_strikes(df)
    support_resistance = _calculate_support_resistance(df, underlying_value)
    oi_buildup_type = _determine_oi_buildup_type(df)

    # Convert strike-wise PCR Series to dictionary
    strike_wise_pcr_dict = strike_wise_pcr.dropna().to_dict()

    # Build result dictionary
    result: Dict[str, Any] = {
        "atm_strike": atm_strike,
        "overall_pcr": overall_pcr,
        "strike_wise_pcr": strike_wise_pcr_dict,
        "max_call_oi_strike": max_oi_strikes["max_call_oi_strike"],
        "max_put_oi_strike": max_oi_strikes["max_put_oi_strike"],
        "support": support_resistance["support"],
        "resistance": support_resistance["resistance"],
        "oi_buildup_type": oi_buildup_type,
    }

    # Add underlying value if available
    if underlying_value is not None:
        result["underlying_value"] = underlying_value

    return result
