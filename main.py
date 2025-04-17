# main.py - Agentic Trading System

# This system implements an autonomous trading workflow with the following components:
# 1. User Interface Agent: Gets trading strategy from the user
# 2. Strategy Agent: Interprets the strategy into structured rules
# 3. Market Data Agent: Fetches market data (live or historical)
# 4. Trading Logic Agent: Watches market data and makes trading decisions
# 5. Portfolio Management Agent: Executes trades and tracks portfolio

from langgraph.graph import StateGraph, END
from agents.user_interface_agent import get_user_strategy
from agents.market_data_agent import check_market_hours,market_data_router, websocket_data, historical_data, simulated_websocket_data, simulated_historical_data
from agents.strategy_agent import interpret_strategy
from agents.trading_logic_agent import watch_market, start_watching, stop_watching
from agents.portfolio_management_agent import initialize_portfolio, execute_trade
import time
from typing import Literal, TypedDict, Dict, Any, List, Optional

class AgentState(TypedDict):
    user_strategy: str
    interpreted_rules: Optional[Dict[str, Any]]
    market_data: Optional[Dict[str, Any]]  # Changed to Any to accommodate different data formats
    portfolio: Optional[Dict[str, int]]
    cash: Optional[float]  # Added cash for portfolio management
    transaction_history: Optional[List[Dict[str, Any]]]  # Changed to typed list
    trade_signal: Optional[Dict[str, Any]]  # Added to store trade signals
    invalid_strategy: Optional[bool]
    report: Optional[str]
    market_open: Optional[bool]  # flag that determines market status
    messages: Optional[List[Dict[str, Any]]] | None  # Changed to typed list


workflow = StateGraph(AgentState)

# Add all nodes to the workflow
workflow.add_node("user_interface", get_user_strategy)
workflow.add_node("strategy_interpretation", interpret_strategy)
workflow.add_node("initialize_portfolio", initialize_portfolio)
workflow.add_node("start_watching", start_watching)

# Market data nodes
workflow.add_node("check_market_hours", check_market_hours)  # Router node
workflow.add_node("websocket_data", websocket_data)  # Live data node
workflow.add_node("simulated_websocket_data", simulated_websocket_data)  # Live data node
workflow.add_node("historical_data", historical_data)  # Historical data node
workflow.add_node("simulated_historical_data", simulated_historical_data)  # Historical data node

# Trading nodes
workflow.add_node("watch_market", watch_market)
workflow.add_node("execute_trade", execute_trade)
workflow.add_node("stop_watching", stop_watching)

workflow.set_entry_point("user_interface")
def should_reprompt_user(state: Dict[str, Any]) -> Literal["user_interface", "strategy_interpretation"]:
    """Determines whether to reprompt the user based on the LLM's classification."""
    print(state.get("invalid_strategy"))
    if state.get("invalid_strategy"):
        return 'user_interface'
    else:
        return 'strategy_interpretation'



# Define the entry point conditional edge
workflow.add_conditional_edges(
    "user_interface",
    should_reprompt_user
)
workflow.add_conditional_edges(
    "check_market_hours",
    market_data_router
)

# Step 1: User query → Strategy interpretation
workflow.add_edge("strategy_interpretation", "initialize_portfolio")

# Step 2: Initialize portfolio and start market data agent
workflow.add_edge("initialize_portfolio", "start_watching")

# Step 3: Start market data flow with router
workflow.add_edge("start_watching", "check_market_hours")

# Connect both data sources to the trading logic
workflow.add_edge("websocket_data", "watch_market")
workflow.add_edge("historical_data", "watch_market")
workflow.add_edge("simulated_websocket_data", "watch_market")
workflow.add_edge("simulated_historical_data", "watch_market")

# Step 5: Trading logic executes trades when conditions are met
workflow.add_edge("watch_market", "execute_trade")

# Step 6: After trade execution, decide whether to continue watching or stop
def should_continue_watching(state: Dict[str, Any]) -> Literal["watch_market", "stop_watching"]:
    """Determines whether to continue watching the market or stop."""
    # Only continue if we're still in watching mode and haven't hit any stopping criteria
    if state.get("is_watching", False):
        print("Still watching the market for more opportunities...")
        return "watch_market"
    else:
        print("Strategy conditions met. Stopping market watch.")
        return "stop_watching"

workflow.add_conditional_edges(
    "execute_trade",
    should_continue_watching
)

# Step 7: Stop watching ends the workflow
workflow.add_edge("stop_watching", END)



# Compile the graph
app = workflow.compile()


# Run the trading system
if __name__ == "__main__":
    print("\n=== Agentic Trading System ===\n")
    print("This system will:")
    print("1. Ask for your trading strategy")
    print("2. Interpret your strategy into structured rules")
    print("3. Start watching the market for trading opportunities")
    print("4. Execute trades when your strategy conditions are met")
    print("5. Stop automatically when the strategy is fully executed")
    print("\nInitializing system...\n")

    # Initialize the state with default values
    inputs = {
        "messages": [],
        "market_data": {},
        "market_open": False,
        "user_strategy": "",
        "interpreted_rules": {},
        "portfolio": {},  # Current holdings
        "cash": 100000.0,  # Starting with $100,000
        "transaction_history": [],
        "trade_signal": {},
        "report": "",
        "invalid_strategy": False,
        "is_watching": False  # Start with watching disabled
    }

    # Invoke the workflow
    print("Starting trading workflow...\n")
    result = app.invoke(inputs)

    # Print the final state
    print("\n=== Trading Session Complete ===\n")
    print(f"Final Portfolio: {result['portfolio']}")
    print(f"Cash Balance: ${result['cash']:.2f}")

    # If still watching, provide a way to manually stop
    if result.get('is_watching', False):
        print("\nTrading agent is still autonomously watching the market.")
        print("It will continue to monitor until the strategy is fully executed.")
        print("Press Ctrl+C to manually stop watching and exit.")

    # If the agent is still watching, keep the process alive until a keyboard interrupt or until watching stops
    if result.get('is_watching', False):
        try:
            print("\nKeeping process alive while trading agent watches the market...")
            print("Press Ctrl+C to stop watching and exit.")

            # Check every second if we're still watching
            while result.get('is_watching', False):
                time.sleep(1)
                # We could periodically check the state here if needed

        except KeyboardInterrupt:
            print("\nManually stopping the trading agent...")
            # Call stop_watching directly to ensure proper shutdown
            stop_watching(result)
            print("Market data connections closed.")

    print("\nTrading session ended. Thank you for using the Agentic Trading System!")
