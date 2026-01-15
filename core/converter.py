"""Convert NSE option chain JSON to pandas DataFrame."""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def _safe_get_value(data: Dict[str, Any] | None, key: str, default: Any = None) -> Any:
    """Safely get a value from a dictionary, returning default if missing or None."""
    if data is None or not isinstance(data, dict):
        return default
    return data.get(key, default)


def _extract_option_data(
    option_data: Dict[str, Any] | None,
    strike_price: float | None,
) -> Dict[str, Any]:
    """Extract relevant fields from option data (CE or PE).

    Args:
        option_data: Dictionary containing CE or PE option data.
        strike_price: Strike price to use if not present in option_data.

    Returns:
        Dictionary with extracted option fields.
    """
    if option_data is None or not isinstance(option_data, dict):
        return {
            "oi": None,
            "oi_change": None,
            "volume": None,
            "iv": None,
        }

    # NSE API field names mapping to our column names
    return {
        "oi": _safe_get_value(option_data, "openInterest"),
        "oi_change": _safe_get_value(option_data, "changeinOpenInterest"),
        "volume": _safe_get_value(option_data, "totalTradedVolume"),
        "iv": _safe_get_value(option_data, "impliedVolatility"),
        "strike_price": _safe_get_value(option_data, "strikePrice", strike_price),
    }


def convert_to_dataframe(data: Dict[str, Any]) -> pd.DataFrame:
    """Convert raw NSE option chain JSON into a pandas DataFrame.

    Creates a DataFrame with one row per strike price, containing both
    call (CE) and put (PE) option data side by side.

    Args:
        data: Raw JSON dictionary from NSE API (should be validated).

    Returns:
        DataFrame with columns:
        - strike_price: Strike price for the option
        - call_oi: Call option open interest
        - call_oi_change: Change in call option open interest
        - call_volume: Call option total traded volume
        - call_iv: Call option implied volatility
        - put_oi: Put option open interest
        - put_oi_change: Change in put option open interest
        - put_volume: Put option total traded volume
        - put_iv: Put option implied volatility

    Raises:
        KeyError: If required keys are missing from data.
        ValueError: If data structure is invalid.
    """
    if not isinstance(data, dict):
        raise ValueError("Data must be a dictionary")

    if "records" not in data:
        raise KeyError("Missing 'records' key in data")

    records = data["records"]
    if not isinstance(records, dict):
        raise ValueError("'records' must be a dictionary")

    if "data" not in records:
        raise KeyError("Missing 'data' key in records")

    records_data = records["data"]
    if not isinstance(records_data, list):
        raise ValueError("'records.data' must be a list")

    if len(records_data) == 0:
        # Return empty DataFrame with correct columns
        return pd.DataFrame(
            columns=[
                "strike_price",
                "call_oi",
                "call_oi_change",
                "call_volume",
                "call_iv",
                "put_oi",
                "put_oi_change",
                "put_volume",
                "put_iv",
            ]
        )

    rows = []

    for record in records_data:
        if not isinstance(record, dict):
            continue

        # Extract CE (Call) and PE (Put) data
        ce_data = record.get("CE")
        pe_data = record.get("PE")

        # Get strike price from CE, PE, or record itself
        strike_price = None
        if ce_data and isinstance(ce_data, dict):
            strike_price = _safe_get_value(ce_data, "strikePrice")
        if strike_price is None and pe_data and isinstance(pe_data, dict):
            strike_price = _safe_get_value(pe_data, "strikePrice")
        if strike_price is None:
            # Skip records without strike price
            continue

        # Extract call option data
        call_data = _extract_option_data(ce_data, strike_price)

        # Extract put option data
        put_data = _extract_option_data(pe_data, strike_price)

        # Create row with both call and put data
        row = {
            "strike_price": strike_price,
            "call_oi": call_data["oi"],
            "call_oi_change": call_data["oi_change"],
            "call_volume": call_data["volume"],
            "call_iv": call_data["iv"],
            "put_oi": put_data["oi"],
            "put_oi_change": put_data["oi_change"],
            "put_volume": put_data["volume"],
            "put_iv": put_data["iv"],
        }

        rows.append(row)

    if len(rows) == 0:
        # Return empty DataFrame with correct columns if no valid rows
        return pd.DataFrame(
            columns=[
                "strike_price",
                "call_oi",
                "call_oi_change",
                "call_volume",
                "call_iv",
                "put_oi",
                "put_oi_change",
                "put_volume",
                "put_iv",
            ]
        )

    # Create DataFrame and sort by strike price
    df = pd.DataFrame(rows)
    df = df.sort_values("strike_price").reset_index(drop=True)

    # Ensure numeric types for numeric columns
    numeric_columns = [
        "strike_price",
        "call_oi",
        "call_oi_change",
        "call_volume",
        "call_iv",
        "put_oi",
        "put_oi_change",
        "put_volume",
        "put_iv",
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    return df
