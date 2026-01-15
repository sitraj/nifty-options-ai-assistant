"""Backtesting engine for options trading."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd


@dataclass
class Trade:
    """Represents a single trade."""

    date: str
    entry_date: str
    exit_date: str | None
    option_type: str  # "CE" or "PE"
    strike_price: float
    entry_price: float
    exit_price: float | None
    quantity: int
    stop_loss: float
    target: float
    underlying_entry: float
    underlying_exit: float | None
    pnl: float | None
    pnl_percent: float | None
    exit_reason: str | None  # "SL", "Target", "Expiry", "Manual"
    status: str  # "Open", "Closed", "Expired"


@dataclass
class BacktestResult:
    """Results from backtesting."""

    trades: List[Trade]
    equity_curve: pd.DataFrame
    win_rate: float
    max_drawdown: float
    total_pnl: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    profit_factor: float
    initial_capital: float
    final_capital: float
    total_return: float


def _get_atm_option_price(
    df: pd.DataFrame,
    atm_strike: float,
    option_type: str,
    price_type: str = "lastPrice",
) -> float | None:
    """Get option price for ATM strike.

    Args:
        df: DataFrame with option chain data.
        atm_strike: ATM strike price.
        option_type: "CE" or "PE".
        price_type: Price field to use (default: "lastPrice").

    Returns:
        Option price or None if not found.
    """
    if df.empty or "strike_price" not in df.columns:
        return None

    # Find row with matching strike
    strike_rows = df[df["strike_price"] == atm_strike]
    if strike_rows.empty:
        return None

    row = strike_rows.iloc[0]

    # Get price based on option type
    if option_type == "CE":
        # Try to get from call_iv or estimate from underlying
        # For backtesting, we'll need to extract from raw data
        # For now, return None and handle in calling function
        return None
    else:  # PE
        return None

    # Note: This function needs raw data to get actual option prices
    # For now, we'll handle price extraction differently


def _extract_option_price_from_raw(
    raw_data: Dict[str, Any],
    strike_price: float,
    option_type: str,
) -> float | None:
    """Extract option price from raw NSE data.

    Args:
        raw_data: Raw JSON dictionary from NSE API.
        strike_price: Strike price to find.
        option_type: "CE" or "PE".

    Returns:
        Option last price or None if not found.
    """
    if "records" not in raw_data:
        return None

    records = raw_data["records"]
    if not isinstance(records, dict):
        return None

    records_data = records.get("data", [])
    if not isinstance(records_data, list):
        return None

    for record in records_data:
        if not isinstance(record, dict):
            continue

        option_data = record.get(option_type)
        if not option_data or not isinstance(option_data, dict):
            continue

        strike = option_data.get("strikePrice")
        if strike is None:
            continue

        try:
            strike_float = float(strike)
            if abs(strike_float - strike_price) < 0.01:  # Allow small floating point differences
                last_price = option_data.get("lastPrice")
                if last_price is not None:
                    try:
                        return float(last_price)
                    except (ValueError, TypeError):
                        pass
        except (ValueError, TypeError):
            continue

    return None


def _calculate_option_exit_price(
    underlying_entry: float,
    underlying_exit: float,
    strike_price: float,
    option_type: str,
    entry_price: float,
    stop_loss: float,
    target: float,
) -> tuple[float, str]:
    """Calculate exit price based on underlying movement and SL/Target.

    Args:
        underlying_entry: Underlying price at entry.
        underlying_exit: Underlying price at exit.
        strike_price: Option strike price.
        option_type: "CE" or "PE".
        entry_price: Option entry price.
        stop_loss: Stop loss percentage (e.g., 0.20 for 20%).
        target: Target percentage (e.g., 0.50 for 50%).
        entry_price: Entry price of option.

    Returns:
        Tuple of (exit_price, exit_reason).
    """
    # Calculate intrinsic value at exit
    if option_type == "CE":
        intrinsic_value = max(0, underlying_exit - strike_price)
    else:  # PE
        intrinsic_value = max(0, strike_price - underlying_exit)

    # For simplicity, assume exit price = intrinsic value + some time value
    # In reality, this would depend on IV, time to expiry, etc.
    # For backtesting, we'll use a simplified model
    exit_price_estimate = intrinsic_value

    # Check if SL or Target hit
    pnl_percent = (exit_price_estimate - entry_price) / entry_price if entry_price > 0 else 0

    if pnl_percent <= -stop_loss:
        # Stop loss hit
        exit_price = entry_price * (1 - stop_loss)
        return exit_price, "SL"
    elif pnl_percent >= target:
        # Target hit
        exit_price = entry_price * (1 + target)
        return exit_price, "Target"
    else:
        # Exit at current price
        return exit_price_estimate, "Manual"


def simulate_trade(
    date: str,
    raw_data: Dict[str, Any],
    features: Dict[str, Any],
    evaluation: Any,  # EvaluationResult
    stop_loss: float = 0.20,  # 20% stop loss
    target: float = 0.50,  # 50% target
    quantity: int = 1,
) -> Trade | None:
    """Simulate a single trade.

    Args:
        date: Trade date.
        raw_data: Raw NSE data for entry.
        features: Features dictionary.
        evaluation: Evaluation result from rule engine.
        stop_loss: Stop loss as percentage (default: 0.20 for 20%).
        target: Target as percentage (default: 0.50 for 50%).
        quantity: Number of lots/contracts.

    Returns:
        Trade object or None if trade cannot be executed.
    """
    # Check if we should trade
    if evaluation.trade_recommendation == "No Trade":
        return None

    # Get ATM strike
    atm_strike = features.get("atm_strike")
    underlying_entry = features.get("underlying_value")

    if atm_strike is None or underlying_entry is None:
        return None

    # Determine option type
    option_type = "CE" if evaluation.trade_recommendation == "Call" else "PE"

    # Get entry price
    entry_price = _extract_option_price_from_raw(raw_data, atm_strike, option_type)
    if entry_price is None or entry_price <= 0:
        # If price not available, skip trade
        return None

    # Create trade
    trade = Trade(
        date=date,
        entry_date=date,
        exit_date=None,
        option_type=option_type,
        strike_price=atm_strike,
        entry_price=entry_price,
        exit_price=None,
        quantity=quantity,
        stop_loss=stop_loss,
        target=target,
        underlying_entry=underlying_entry,
        underlying_exit=None,
        pnl=None,
        pnl_percent=None,
        exit_reason=None,
        status="Open",
    )

    return trade


def close_trade(
    trade: Trade,
    exit_date: str,
    raw_data: Dict[str, Any],
    features: Dict[str, Any],
) -> Trade:
    """Close a trade.

    Args:
        trade: Trade to close.
        exit_date: Exit date.
        raw_data: Raw NSE data for exit.
        features: Features dictionary for exit.

    Returns:
        Updated trade with exit information.
    """
    underlying_exit = features.get("underlying_value")
    if underlying_exit is None:
        underlying_exit = trade.underlying_entry

    # Calculate exit price
    exit_price, exit_reason = _calculate_option_exit_price(
        trade.underlying_entry,
        underlying_exit,
        trade.strike_price,
        trade.option_type,
        trade.entry_price,
        trade.stop_loss,
        trade.target,
    )

    # Calculate P&L
    pnl = (exit_price - trade.entry_price) * trade.quantity
    pnl_percent = (exit_price - trade.entry_price) / trade.entry_price if trade.entry_price > 0 else 0

    # Update trade
    trade.exit_date = exit_date
    trade.exit_price = exit_price
    trade.underlying_exit = underlying_exit
    trade.pnl = pnl
    trade.pnl_percent = pnl_percent
    trade.exit_reason = exit_reason
    trade.status = "Closed"

    return trade


def run_backtest(
    daily_data: List[Dict[str, Any]],
    initial_capital: float = 100000.0,
    stop_loss: float = 0.20,
    target: float = 0.50,
    quantity: int = 1,
    max_open_trades: int = 1,
) -> BacktestResult:
    """Run backtest on historical data.

    Args:
        daily_data: List of daily data dictionaries, each containing:
            - date: str
            - raw_data: Dict[str, Any]
            - features: Dict[str, Any]
            - evaluation: EvaluationResult
        initial_capital: Starting capital.
        stop_loss: Stop loss percentage (default: 0.20 for 20%).
        target: Target percentage (default: 0.50 for 50%).
        quantity: Number of lots per trade.
        max_open_trades: Maximum open trades at once (default: 1).

    Returns:
        BacktestResult with all statistics.
    """
    trades: List[Trade] = []
    open_trades: List[Trade] = []
    equity_curve_data = []
    current_capital = initial_capital

    # Process each day
    for day_data in daily_data:
        date = day_data["date"]
        raw_data = day_data["raw_data"]
        features = day_data["features"]
        evaluation = day_data["evaluation"]

        # Close existing trades if conditions met
        for trade in open_trades[:]:
            # For simplicity, close all trades at end of day
            # In reality, you'd check SL/Target during the day
            trade = close_trade(trade, date, raw_data, features)
            trades.append(trade)
            open_trades.remove(trade)
            current_capital += trade.pnl if trade.pnl else 0

        # Open new trade if conditions met (one per day, max open trades)
        if len(open_trades) < max_open_trades:
            new_trade = simulate_trade(
                date,
                raw_data,
                features,
                evaluation,
                stop_loss=stop_loss,
                target=target,
                quantity=quantity,
            )

            if new_trade:
                # Check if we have enough capital
                trade_cost = new_trade.entry_price * new_trade.quantity
                if current_capital >= trade_cost:
                    open_trades.append(new_trade)
                    current_capital -= trade_cost

        # Record equity
        equity_curve_data.append({
            "date": date,
            "equity": current_capital,
            "open_trades": len(open_trades),
        })

    # Close any remaining open trades
    if daily_data:
        last_day = daily_data[-1]
        for trade in open_trades:
            trade = close_trade(
                trade,
                last_day["date"],
                last_day["raw_data"],
                last_day["features"],
            )
            trades.append(trade)
            current_capital += trade.pnl if trade.pnl else 0

    # Calculate statistics
    closed_trades = [t for t in trades if t.status == "Closed"]
    total_trades = len(closed_trades)
    winning_trades = [t for t in closed_trades if t.pnl and t.pnl > 0]
    losing_trades = [t for t in closed_trades if t.pnl and t.pnl <= 0]

    win_rate = len(winning_trades) / total_trades if total_trades > 0 else 0.0

    total_pnl = sum(t.pnl for t in closed_trades if t.pnl)
    avg_win = sum(t.pnl for t in winning_trades if t.pnl) / len(winning_trades) if winning_trades else 0.0
    avg_loss = sum(t.pnl for t in losing_trades if t.pnl) / len(losing_trades) if losing_trades else 0.0

    profit_factor = abs(avg_win / avg_loss) if avg_loss != 0 else 0.0

    # Calculate max drawdown
    equity_df = pd.DataFrame(equity_curve_data)
    if not equity_df.empty:
        equity_df["peak"] = equity_df["equity"].cummax()
        equity_df["drawdown"] = (equity_df["equity"] - equity_df["peak"]) / equity_df["peak"]
        max_drawdown = equity_df["drawdown"].min() if not equity_df["drawdown"].isna().all() else 0.0
    else:
        max_drawdown = 0.0

    final_capital = current_capital
    total_return = (final_capital - initial_capital) / initial_capital if initial_capital > 0 else 0.0

    return BacktestResult(
        trades=trades,
        equity_curve=pd.DataFrame(equity_curve_data),
        win_rate=win_rate,
        max_drawdown=max_drawdown,
        total_pnl=total_pnl,
        total_trades=total_trades,
        winning_trades=len(winning_trades),
        losing_trades=len(losing_trades),
        avg_win=avg_win,
        avg_loss=avg_loss,
        profit_factor=profit_factor,
        initial_capital=initial_capital,
        final_capital=final_capital,
        total_return=total_return,
    )


def trades_to_dataframe(trades: List[Trade]) -> pd.DataFrame:
    """Convert list of trades to DataFrame for easy viewing.

    Args:
        trades: List of Trade objects.

    Returns:
        DataFrame with trade details.
    """
    if not trades:
        return pd.DataFrame()

    data = []
    for trade in trades:
        data.append({
            "Date": trade.date,
            "Entry Date": trade.entry_date,
            "Exit Date": trade.exit_date,
            "Option Type": trade.option_type,
            "Strike": trade.strike_price,
            "Entry Price": trade.entry_price,
            "Exit Price": trade.exit_price,
            "Quantity": trade.quantity,
            "Underlying Entry": trade.underlying_entry,
            "Underlying Exit": trade.underlying_exit,
            "P&L": trade.pnl,
            "P&L %": trade.pnl_percent,
            "Exit Reason": trade.exit_reason,
            "Status": trade.status,
        })

    return pd.DataFrame(data)
