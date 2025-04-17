import os
import time
import random
from typing import Literal,Dict, Any, TypedDict
import asyncio
import threading
import queue
from datetime import datetime, timedelta, time as dtime, timezone
import pytz
# Optional: load environment variables from a .env file if desired.
from dotenv import load_dotenv
load_dotenv()

# Import alpaca‑py modules for historical data and live streaming.
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.data.live.stock import StockDataStream

symbols=['AAPL', 'GOOGL', 'BTC', 'TSLA']

# 1. Define the state of our graph.
class AgentState(TypedDict):
    """State for the agent."""
    messages: list[Dict[str, Any]]
    market_data: Dict[str, Any]
    market_open: bool  # flag that determines market status

# 2. Create a threading.Event to signal shutdown.
shutdown_event = threading.Event()

# 3. Create a queue for passing market data updates.
market_data_queue = queue.Queue()

# Define symbols to watch
symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "SPY"]

# Define data handlers that put data into the queue
async def quote_data_handler(data):
    print(f"Received quote data: {data}")
    market_data_queue.put({"type": "quote", "data": data})

async def bars_data_handler(data):
    print(f"Received bar data: {data}")
    market_data_queue.put({"type": "bar", "data": data})

async def trades_data_handler(data):
    print(f"Received trade data: {data}")
    market_data_queue.put({"type": "trade", "data": data})

def shutdown_socket_event():
    print("Shutting down websocket connection...")
    shutdown_event.set()

# 4. Function to run the Alpaca WebSocket stream using alpaca‑py.
def run_websocket(api_key, secret_key, data_feed, shutdown_event, data_queue):
    try:
        client = StockDataStream(key_id=api_key, secret_key=secret_key, data_feed=data_feed)

        # Subscribe to different data types for our symbols
        client.subscribe_bars(bars_data_handler, *symbols)
        client.subscribe_quotes(quote_data_handler, *symbols)
        client.subscribe_trades(trades_data_handler, *symbols)

        print(f"Subscribed to data for symbols: {symbols}")
        print("Starting websocket connection...")

        # Run the websocket client
        client.run()

        # Check for shutdown event
        while not shutdown_event.is_set():
            time.sleep(0.1)

        print("Websocket shutdown event received")
        client.stop()
        print("Websocket connection closed")

    except Exception as e:
        print(f"Error in websocket connection: {e}")
        # Add mock data for testing if the connection fails
        for symbol in symbols:
            mock_price = 150.0 if symbol == "AAPL" else 100.0
            data_queue.put({"type": "bar", "data": {"symbol": symbol, "close": mock_price}})

    print("Websocket thread ending")

# 5. Node: Market Data Agent for live data using alpaca‑py’s live stream.
def alpaca_market_data_agent(state:AgentState):
    print("Starting live market data stream (WebSocket - alpaca‑py)...")
    ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise EnvironmentError("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY as environment variables.")
    data_feed = "iex"  # or "sip" based on your subscription

    # Start the websocket in a separate thread.
    thread = threading.Thread(
        target=run_websocket,
        args=(ALPACA_API_KEY, ALPACA_SECRET_KEY, data_feed, shutdown_event, market_data_queue)
    )
    thread.daemon = True
    thread.start()

    msg = "Live market data stream (WebSocket - alpaca‑py) started."
    if "messages" in state:
        state["messages"].append({"role": "agent", "content": msg})
    else:
        state["messages"] = [{"role": "agent", "content": msg}]
    return state

# 6. Node: Fetch historical data using alpaca‑py.
def fetch_historical_data(state:AgentState):
    print("Fetching historical data from Alpaca API (alpaca‑py)...")
    ALPACA_API_KEY = os.environ.get("ALPACA_API_KEY")
    ALPACA_SECRET_KEY = os.environ.get("ALPACA_SECRET_KEY")
    if not ALPACA_API_KEY or not ALPACA_SECRET_KEY:
        raise EnvironmentError("Please set ALPACA_API_KEY and ALPACA_SECRET_KEY as environment variables.")

    client = StockHistoricalDataClient(ALPACA_API_KEY, ALPACA_SECRET_KEY)
    symbols = ['AAPL', 'GOOGL', 'BTC', 'TSLA']
    end_dt = datetime.now(pytz.utc).date()
    start_dt = end_dt - timedelta(days=100)

    historical_data = {}
    for symbol in symbols:
        print(f"Fetching historical bars for {symbol}...")
        request_params = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=TimeFrame.Day,
            start=start_dt.isoformat(),
            end=end_dt.isoformat()
        )
        bars = client.get_stock_bars(request_params).df
        historical_data[symbol] = bars.to_dict('records')

    msg = "Historical data fetched (alpaca‑py)."
    if "messages" in state:
        state["messages"].append({"role": "agent", "content": msg})
    else:
        state["messages"] = [{"role": "agent", "content": msg}]
    state["market_data"] = {"historical_bars": historical_data}
    return state

# 6b. Node: Fetch historical data using simulated data.
def fetch_simulated_historical_data(state:AgentState):
    print("Fetching simulated historical data...")
    from agents.simulated_data import generate_simulated_data

    try:
        # Generate simulated data
        simulated_data = generate_simulated_data()

        # Add the data to the state
        state["market_data"] = simulated_data

        msg = "Simulated historical data generated successfully."
        if "messages" in state:
            state["messages"].append({"role": "agent", "content": msg})
        else:
            state["messages"] = [{"role": "agent", "content": msg}]
    except Exception as e:
        print(f"Error generating simulated data: {e}")
        msg = f"Error generating simulated data: {e}"
        if "messages" in state:
            state["messages"].append({"role": "agent", "content": msg})
        else:
            state["messages"] = [{"role": "agent", "content": msg}]

    return state

# 7. Node: Check Market Hours and update state with a market_open flag.
def check_market_hours(state:AgentState):
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    market_open_time = dtime(9, 30)
    market_close_time = dtime(16, 0)
    is_weekday = now.weekday() < 5  # Monday=0, Sunday=6

    open_flag = is_weekday and (market_open_time <= now.time() <= market_close_time)
    msg = f"Market open check: Now is {now.strftime('%Y-%m-%d %H:%M:%S')} ET. Market open: {open_flag}"
    print(msg)
    if "messages" in state:
        state["messages"].append({"role": "agent", "content": msg})
    state["market_open"] = open_flag
    return state

# 8. Market Data Router: Conditional node that routes to either websocket or historical data
def market_data_router(state:AgentState) -> Literal["websocket_data", "historical_data", "simulated_websocket_data", "simulated_historical_data"]:
    """Determine the appropriate market data source based on market hours and availability.
    This function acts as a router that returns the next node to execute."""
    # Check if we should use simulated data (for testing when APIs are down)
    use_simulation = state.get("use_simulation", True)  # Default to simulation for now

    # Check if the market is currently open
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    market_open_time = dtime(9, 30)
    market_close_time = dtime(16, 0)
    is_weekday = now.weekday() < 5  # Monday=0, Sunday=6

    open_flag = is_weekday and (market_open_time <= now.time() <= market_close_time)

    print(f"Market data router: Current time is {now.strftime('%Y-%m-%d %H:%M:%S')} ET")
    print(f"Market is {'open' if open_flag else 'closed'}")

    # Update the state with market status
    state["market_open"] = open_flag

    if use_simulation:
        print("Using simulated market data (APIs unavailable)...")
        # Determine which simulated data source to use
        if open_flag:
            print("Routing to simulated live websocket data source...")
            return "simulated_websocket_data"
        else:
            print("Routing to simulated historical data source...")
            return "simulated_historical_data"
    else:
        # Use real API data
        if open_flag:
            print("Routing to live websocket data source...")
            return "websocket_data"
        else:
            print("Routing to historical data source...")
            return "historical_data"

# 9. Node: Process data coming from both the queue (streaming) and batch historical data.
def update_state_with_data(state:AgentState):
    market_data = state.get("market_data", {})

    # Process streaming data from the queue.
    while not market_data_queue.empty():
        data_item = market_data_queue.get()
        data_type = data_item["type"]
        current_list = market_data.get(data_type, [])
        current_list.append(data_item["data"])
        market_data[data_type] = current_list
        market_data_queue.task_done()

    msg = "State updated with streaming and/or historical data."
    if "messages" in state:
        state["messages"].append({"role": "agent", "content": msg})
    else:
        state["messages"] = [{"role": "agent", "content": msg}]
    state["market_data"] = market_data
    return state

# 10. Node: Websocket Data - Live market data using websocket
def websocket_data(state:AgentState):
    """Start a websocket connection to get live market data."""
    print("Starting live market data stream via websocket...")
    # Call the existing alpaca market data agent function
    state = alpaca_market_data_agent(state)
    # Process any initial data
    state = update_state_with_data(state)
    # Set the is_watching flag to true
    state["is_watching"] = True
    print("Websocket data stream established. Trading agent is now watching the market.")
    return state

# 10b. Node: Simulated Websocket Data - Simulated live market data
def simulated_websocket_data(state:AgentState):
    """Start a simulated websocket connection to get live market data."""
    print("Starting simulated live market data stream...")
    from agents.simulated_data import generate_simulated_data

    try:
        # Generate simulated data
        simulated_data = generate_simulated_data()

        # Add the data to the state
        state["market_data"] = simulated_data

        # Start a background thread to continuously update the data
        # We'll simulate this by just adding some initial data

        # Process any initial data
        state = update_state_with_data(state)

        # Set the is_watching flag to true
        state["is_watching"] = True
        print("Simulated data stream established. Trading agent is now watching the market.")
    except Exception as e:
        print(f"Error setting up simulated data stream: {e}")
        msg = f"Error setting up simulated data stream: {e}"
        if "messages" in state:
            state["messages"].append({"role": "agent", "content": msg})
        else:
            state["messages"] = [{"role": "agent", "content": msg}]

    return state

# 11. Node: Historical Data - Fetch historical market data
def historical_data(state:AgentState):
    """Fetch historical market data."""
    print("Fetching historical market data...")
    # Call the existing fetch historical data function
    state = fetch_historical_data(state)
    # Process the data
    state = update_state_with_data(state)
    # Set the is_watching flag to true
    state["is_watching"] = True
    print("Historical data loaded. Trading agent is now watching the market.")
    return state

# 11b. Node: Simulated Historical Data - Fetch simulated historical market data
def simulated_historical_data(state:AgentState):
    """Fetch simulated historical market data."""
    print("Fetching simulated historical market data...")
    from agents.simulated_data import generate_simulated_data

    try:
        # Generate simulated data
        simulated_data = generate_simulated_data()

        # Add the data to the state
        state["market_data"] = simulated_data

        # Process the data
        state = update_state_with_data(state)

        # Set the is_watching flag to true
        state["is_watching"] = True
        print("Simulated historical data loaded. Trading agent is now watching the market.")
    except Exception as e:
        print(f"Error generating simulated historical data: {e}")
        msg = f"Error generating simulated historical data: {e}"
        if "messages" in state:
            state["messages"].append({"role": "agent", "content": msg})
        else:
            state["messages"] = [{"role": "agent", "content": msg}]

    return state

