# agents/trading_logic_agent.py
from typing import TypedDict, Dict, Any, List, Optional
import time

class AgentState(TypedDict):
    interpreted_rules: Dict[str, Any]
    market_data: Dict[str, Any]  # Market data can be historical or live
    trade_signal: Dict[str, Any] # To store the trade signal
    portfolio: Dict[str, int] # We'll need to know our current holdings
    is_watching: bool # Flag to indicate if we're actively watching the market

def get_current_price(market_data: Dict[str, Any], symbol: str) -> Optional[float]:
    """Extract the current price for a symbol from various market data formats."""
    # Try to get price from historical bars first
    if "historical_bars" in market_data and symbol in market_data["historical_bars"]:
        bars = market_data["historical_bars"][symbol]
        if bars and len(bars) > 0:
            return bars[-1].get("close")

    # If not found in historical, try live data bars
    if "bar" in market_data and len(market_data["bar"]) > 0:
        for bar in market_data["bar"]:
            if bar.get("symbol") == symbol:
                return bar.get("close")

    # If still not found, try quotes
    if "quote" in market_data and len(market_data["quote"]) > 0:
        for quote in market_data["quote"]:
            if quote.get("symbol") == symbol:
                # Use mid price from quote
                return (quote.get("ask_price", 0) + quote.get("bid_price", 0)) / 2

    # If still not found, try trades
    if "trade" in market_data and len(market_data["trade"]) > 0:
        for trade in market_data["trade"]:
            if trade.get("symbol") == symbol:
                return trade.get("price")

    return None

def watch_market(state: AgentState):
    """Node for the Trading Logic Agent to continuously watch market data and make trading decisions."""
    interpreted_rules = state.get("interpreted_rules", {})
    market_data = state.get("market_data", {})
    portfolio = state.get("portfolio", {})
    trade_signal = {}
    is_watching = state.get("is_watching", False)

    # If we're not watching, just return the current state
    if not is_watching:
        print("Trading logic agent is not actively watching the market.")
        return {"trade_signal": trade_signal}

    # If we're watching, check for new market data
    print("Trading logic agent is analyzing market data for trading opportunities...")

    # Check if we have market data to analyze
    if not market_data:
        print("No market data available yet. Waiting for data...")
        return {"trade_signal": trade_signal}

    # Check if the strategy has been fully executed
    # If we've already bought and sold according to the strategy, we should stop watching
    transaction_history = state.get("transaction_history", [])

    # Check if we've completed a full buy-sell cycle for the strategy
    buy_executed = False
    sell_executed = False

    for transaction in transaction_history:
        if transaction.get("status") == "executed":
            if transaction.get("action") == "buy":
                buy_executed = True
            elif transaction.get("action") == "sell":
                sell_executed = True

    # If we've both bought and sold according to the strategy, stop watching
    if buy_executed and sell_executed:
        print("Strategy fully executed (buy and sell completed). Stopping market watch.")
        return {"trade_signal": trade_signal, "is_watching": False}

    # Get the strategy directly from the interpreted rules
    strategy = interpreted_rules.get("strategy", {})
    raw_output = interpreted_rules.get("raw_output", "")

    print(f"Raw strategy output: {raw_output}")
    print(f"Strategy JSON: {strategy}")

    # If no strategy was found, return without a trade signal
    if not strategy:
        print("No strategy found in the interpreted rules.")
        return {"trade_signal": trade_signal}

    # Extract the asset symbol from the strategy
    asset = strategy.get("asset")
    if not asset:
        print("No asset specified in the strategy.")
        return {"trade_signal": trade_signal}

    # Get the entry and exit conditions
    entry_condition = strategy.get("entry_condition", {})
    exit_condition = strategy.get("exit_condition", {})

    # Get current price for the asset
    current_price = get_current_price(market_data, asset)
    if current_price is None:
        print(f"No market data found for asset: {asset}")
        return {"trade_signal": trade_signal}

    print(f"Current price of {asset}: {current_price}")

    # Process entry condition (buy signal)
    if entry_condition and entry_condition.get("type") == "price_trigger" and portfolio.get(asset, 0) == 0:
        condition_type = entry_condition.get("condition")
        trigger_price = entry_condition.get("price")
        description = entry_condition.get("description", "")

        print(f"Checking buy condition: {condition_type} {trigger_price} ({description})")

        should_buy = False
        if condition_type == "below" and current_price < trigger_price:
            should_buy = True
        elif condition_type == "above" and current_price > trigger_price:
            should_buy = True
        elif condition_type == "equal" and abs(current_price - trigger_price) < 0.01:  # Small tolerance
            should_buy = True

        if should_buy:
            trade_signal = {"action": "buy", "symbol": asset, "quantity": 10}  # Buy 10 shares
            print(f"Generated BUY signal: {trade_signal}")

    # Process exit condition (sell signal)
    if exit_condition and exit_condition.get("type") == "price_trigger" and portfolio.get(asset, 0) > 0:
        condition_type = exit_condition.get("condition")
        trigger_price = exit_condition.get("price")
        description = exit_condition.get("description", "")

        print(f"Checking sell condition: {condition_type} {trigger_price} ({description})")

        should_sell = False
        if condition_type == "below" and current_price < trigger_price:
            should_sell = True
        elif condition_type == "above" and current_price > trigger_price:
            should_sell = True
        elif condition_type == "equal" and abs(current_price - trigger_price) < 0.01:  # Small tolerance
            should_sell = True

        if should_sell:
            trade_signal = {"action": "sell", "symbol": asset, "quantity": portfolio.get(asset, 0)}
            print(f"Generated SELL signal: {trade_signal}")

    # Return the updated state with the trade signal
    return {"trade_signal": trade_signal}

def start_watching(state: AgentState):
    """Start watching the market for trading opportunities."""
    print("Starting to watch the market for trading opportunities...")
    return {"is_watching": True}

def stop_watching(state: AgentState):
    """Stop watching the market and shutdown market data connections."""
    from agents.market_data_agent import shutdown_socket_event

    print("Strategy execution complete. Stopping market watch and shutting down market data connections...")
    print(f"Final portfolio: {state.get('portfolio', {})}")
    print(f"Cash balance: ${state.get('cash', 0):.2f}")

    # Trigger the shutdown event for any active market data connections
    shutdown_socket_event()

    # Generate a simple report of the trading activity
    transaction_history = state.get("transaction_history", [])
    if transaction_history:
        print("\nTransaction History:")
        for i, transaction in enumerate(transaction_history, 1):
            print(f"  {i}. {transaction.get('action', '').upper()} {transaction.get('quantity', 0)} shares of "
                  f"{transaction.get('symbol', '')} at ${transaction.get('price', 0):.2f} "
                  f"(${transaction.get('value', 0):.2f})")

    return {"is_watching": False}