import os
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
from alpaca.data.live import StockDataStream

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

def shutdown_socket_event():
    shutdown_event.set()

# 4. Function to run the Alpaca WebSocket stream using alpaca‑py.
def run_websocket(api_key, secret_key, data_feed, shutdown_event, data_queue):
    client = StockDataStream(key_id=api_key, secret_key=secret_key, data_feed=data_feed)
    async def main():
        # Subscribe to bars, quotes, and trades.
        await client.subscribe_bars(['AAPL', 'GOOGL', 'BTC', 'TSLA'])
        await client.subscribe_quotes(['AAPL', 'GOOGL', 'BTC', 'TSLA'])
        await client.subscribe_trades(['AAPL', 'GOOGL', 'BTC', 'TSLA'])
        print("alpaca‑py live stream subscriptions active.")
        # Run until a shutdown is signaled.
        while not shutdown_event.is_set():
            await asyncio.sleep(1)
        await client.stop()
        print("alpaca‑py live stream stopped.")

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(main())
    loop.close()

# 5. Node: Market Data Agent for live data using alpaca‑py’s live stream.
def alpaca_market_data_agent(state):
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
    state["messages"].append({"role": "agent", "content": msg})
    return state

# 6. Node: Fetch historical data using alpaca‑py.
def fetch_historical_data(state):
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
    state["messages"].append({"role": "agent", "content": msg})
    state["market_data"] = {"historical_bars": historical_data}
    return state

# 7. Node: Check Market Hours and update state with a market_open flag.
def check_market_hours(state):
    eastern = pytz.timezone("US/Eastern")
    now = datetime.now(eastern)
    market_open_time = dtime(9, 30)
    market_close_time = dtime(16, 0)
    is_weekday = now.weekday() < 5  # Monday=0, Sunday=6

    open_flag = is_weekday and (market_open_time <= now.time() <= market_close_time)
    msg = f"Market open check: Now is {now.strftime('%Y-%m-%d %H:%M:%S')} ET. Market open: {open_flag}"
    print(msg)
    state["messages"].append({"role": "agent", "content": msg})
    state["market_open"] = open_flag
    return state

# 8. Market Data Router: Conditional node that routes to either websocket or historical data
def market_data_router(state) -> Literal["historical_data", "websocket_data"]:
    """Determine the appropriate market data source based on market hours.
    This function acts as a router that returns the next node to execute."""
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

    # Based on market hours, determine which data source to use
    if open_flag:
        print("Routing to live websocket data source...")
        return "websocket_data"
    else:
        print("Routing to historical data source...")
        return "historical_data"

# 9. Node: Process data coming from both the queue (streaming) and batch historical data.
def update_state_with_data(state):
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
    state["messages"].append({"role": "agent", "content": msg})
    state["market_data"] = market_data
    return state

# 10. Node: Websocket Data - Live market data using websocket
def websocket_data(state):
    """Start a websocket connection to get live market data."""
    print("Starting live market data stream via websocket...")
    # Call the existing alpaca market data agent function
    state = alpaca_market_data_agent(state)
    # Process any initial data
    return update_state_with_data(state)

# 11. Node: Historical Data - Fetch historical market data
def historical_data(state):
    """Fetch historical market data."""
    print("Fetching historical market data...")
    # Call the existing fetch historical data function
    state = fetch_historical_data(state)
    # Process the data
    return update_state_with_data(state)

