# agents/portfolio_management_agent.py
from typing import TypedDict, Dict, Any, List
from datetime import datetime
import json

class AgentState(TypedDict):
    trade_signal: Dict[str, Any]  # Signal from trading logic agent
    portfolio: Dict[str, int]  # Current portfolio holdings
    cash: float  # Available cash
    transaction_history: List[Dict[str, Any]]  # History of all transactions
    report: str  # Portfolio performance report

def initialize_portfolio(state: AgentState):
    """Initialize the portfolio with starting cash and empty holdings."""
    if "portfolio" not in state or not state["portfolio"]:
        state["portfolio"] = {}
    
    if "cash" not in state:
        state["cash"] = 100000.0  # Starting with $100,000
    
    if "transaction_history" not in state:
        state["transaction_history"] = []
    
    return state

def execute_trade(state: AgentState):
    """Execute the trade based on the signal from the trading logic agent."""
    trade_signal = state.get("trade_signal", {})
    portfolio = state.get("portfolio", {})
    cash = state.get("cash", 100000.0)
    transaction_history = state.get("transaction_history", [])
    
    if not trade_signal:
        print("No trade signal received.")
        return state
    
    action = trade_signal.get("action")
    symbol = trade_signal.get("symbol")
    quantity = trade_signal.get("quantity", 0)
    
    if not action or not symbol or quantity <= 0:
        print(f"Invalid trade signal: {trade_signal}")
        return state
    
    # Get the latest price for the symbol from market data
    market_data = state.get("market_data", {})
    current_price = None
    
    # Try to get price from historical bars first
    if "historical_bars" in market_data and symbol in market_data["historical_bars"]:
        bars = market_data["historical_bars"][symbol]
        if bars and len(bars) > 0:
            current_price = bars[-1].get("close")
    
    # If not found in historical, try live data
    if current_price is None and "bar" in market_data and len(market_data["bar"]) > 0:
        for bar in market_data["bar"]:
            if bar.get("symbol") == symbol:
                current_price = bar.get("close")
                break
    
    # If still not found, try quotes
    if current_price is None and "quote" in market_data and len(market_data["quote"]) > 0:
        for quote in market_data["quote"]:
            if quote.get("symbol") == symbol:
                # Use mid price from quote
                current_price = (quote.get("ask_price", 0) + quote.get("bid_price", 0)) / 2
                break
    
    # If still not found, try trades
    if current_price is None and "trade" in market_data and len(market_data["trade"]) > 0:
        for trade in market_data["trade"]:
            if trade.get("symbol") == symbol:
                current_price = trade.get("price")
                break
    
    if current_price is None:
        print(f"Could not determine current price for {symbol}")
        return state
    
    transaction = {
        "timestamp": datetime.now().isoformat(),
        "action": action,
        "symbol": symbol,
        "quantity": quantity,
        "price": current_price,
        "value": quantity * current_price
    }
    
    if action == "buy":
        # Check if we have enough cash
        cost = quantity * current_price
        if cost > cash:
            print(f"Insufficient funds to buy {quantity} shares of {symbol} at ${current_price}")
            transaction["status"] = "failed"
            transaction["reason"] = "insufficient_funds"
        else:
            # Update portfolio and cash
            portfolio[symbol] = portfolio.get(symbol, 0) + quantity
            cash -= cost
            transaction["status"] = "executed"
            print(f"Bought {quantity} shares of {symbol} at ${current_price}")
    
    elif action == "sell":
        # Check if we have enough shares
        current_shares = portfolio.get(symbol, 0)
        if quantity > current_shares:
            print(f"Insufficient shares to sell {quantity} shares of {symbol}")
            transaction["status"] = "failed"
            transaction["reason"] = "insufficient_shares"
        else:
            # Update portfolio and cash
            portfolio[symbol] = current_shares - quantity
            cash += quantity * current_price
            transaction["status"] = "executed"
            print(f"Sold {quantity} shares of {symbol} at ${current_price}")
            
            # Remove symbol from portfolio if no shares left
            if portfolio[symbol] == 0:
                del portfolio[symbol]
    
    # Add transaction to history
    transaction_history.append(transaction)
    
    # Update state
    state["portfolio"] = portfolio
    state["cash"] = cash
    state["transaction_history"] = transaction_history
    
    # Generate a report
    state["report"] = generate_portfolio_report(state)
    
    return state

def generate_portfolio_report(state: AgentState) -> str:
    """Generate a report of the current portfolio status."""
    portfolio = state.get("portfolio", {})
    cash = state.get("cash", 0)
    transaction_history = state.get("transaction_history", [])
    market_data = state.get("market_data", {})
    
    # Calculate total portfolio value
    portfolio_value = cash
    holdings_details = []
    
    for symbol, quantity in portfolio.items():
        # Get the latest price for the symbol
        current_price = None
        
        # Try to get price from historical bars first
        if "historical_bars" in market_data and symbol in market_data["historical_bars"]:
            bars = market_data["historical_bars"][symbol]
            if bars and len(bars) > 0:
                current_price = bars[-1].get("close")
        
        # If not found in historical, try live data
        if current_price is None and "bar" in market_data and len(market_data["bar"]) > 0:
            for bar in market_data["bar"]:
                if bar.get("symbol") == symbol:
                    current_price = bar.get("close")
                    break
        
        # If still not found, try quotes
        if current_price is None and "quote" in market_data and len(market_data["quote"]) > 0:
            for quote in market_data["quote"]:
                if quote.get("symbol") == symbol:
                    current_price = (quote.get("ask_price", 0) + quote.get("bid_price", 0)) / 2
                    break
        
        # If still not found, try trades
        if current_price is None and "trade" in market_data and len(market_data["trade"]) > 0:
            for trade in market_data["trade"]:
                if trade.get("symbol") == symbol:
                    current_price = trade.get("price")
                    break
        
        if current_price is not None:
            position_value = quantity * current_price
            portfolio_value += position_value
            holdings_details.append({
                "symbol": symbol,
                "quantity": quantity,
                "price": current_price,
                "value": position_value
            })
    
    # Calculate performance metrics
    total_invested = 100000.0  # Starting cash
    profit_loss = portfolio_value - total_invested
    profit_loss_percentage = (profit_loss / total_invested) * 100 if total_invested > 0 else 0
    
    # Generate report
    report = {
        "timestamp": datetime.now().isoformat(),
        "cash": cash,
        "holdings": holdings_details,
        "portfolio_value": portfolio_value,
        "profit_loss": profit_loss,
        "profit_loss_percentage": profit_loss_percentage,
        "transaction_count": len(transaction_history),
        "last_transaction": transaction_history[-1] if transaction_history else None
    }
    
    return json.dumps(report, indent=2)
