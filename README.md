# Agentic Trading System

An autonomous trading system built with LangGraph that uses agent-based architecture to execute trading strategies based on natural language instructions.

## Workflow Diagram

The following diagram illustrates the system's workflow:

![Agentic Trading System Workflow](https://github.com/mdaffan/multi-agent-stock-trading/blob/e883e7bc918b65476fb87afe43911c32acccd78c/workflow.png)
![Agentic Trading System Workflow](https://github.com/mdaffan/multi-agent-stock-trading/blob/4d6e154b0c022c474db7a16f51bcd6be9f95cbad/demo-trade.mp4)

*Note: The demo video is included in the repository. You can view it after cloning the repo.*

The workflow follows these steps:

1. User provides a trading strategy via the user interface
2. Strategy is interpreted into structured rules
3. Portfolio is initialized
4. Market data agent starts watching (with router deciding between websocket or historical data)
5. Trading logic agent monitors the market and makes decisions
6. When conditions are met, trades are executed
7. When the strategy is complete, the system stops watching

## Overview

This system implements a workflow of specialized agents that work together to:

1. Interpret natural language trading strategies
2. Fetch market data (live or historical)
3. Monitor the market for trading opportunities
4. Execute trades when conditions are met
5. Track portfolio performance

## Architecture

The system consists of the following components:

- **User Interface Agent**: Gets trading strategy from the user
- **Strategy Agent**: Interprets the strategy into structured rules
- **Market Data Agent**: Fetches market data (live or historical)
- **Trading Logic Agent**: Watches market data and makes trading decisions
- **Portfolio Management Agent**: Executes trades and tracks portfolio

## Installation

This project uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver that significantly improves dependency management.

```bash
# Install uv if you don't have it
# Create and activate a virtual environment
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv
```

## Configuration

To use live market data from Alpaca, set the following environment variables:

```bash
export ALPACA_API_KEY="your_api_key"
export ALPACA_SECRET_KEY="your_secret_key"
```

Alternatively, create a `.env` file in the project root with these variables.

## Usage

Ingest the knowledge data for you RAG onto your chroma-db

```bash
python ingest-algo-strategies.py
```

Run the trading system:

```bash
python main.py
```

The system will prompt you for a trading strategy and then execute it autonomously.


## Example Prompts

Here are some example trading strategies you can use:

### Simple Price Trigger

```text
Buy 10 shares of AAPL when the price goes above $180, and sell when it reaches $190.
```

### Moving Average Strategy

```text
Buy TSLA when the 5-day moving average crosses above the 20-day moving average, and sell when it crosses below.
```

### Volume-Based Strategy

```text
Buy MSFT when the trading volume is 20% higher than the 10-day average volume, and sell after a 5% profit.
```

### Multiple Conditions

```text
Buy GOOGL when the price drops below $140 AND the RSI is below 30, then sell when the price increases by 7%.
```

### Sector Rotation

```text
Buy SPY when the technology sector (XLK) outperforms the utilities sector (XLU) by 5% over the last month, and sell when this trend reverses.
```

## Simulated vs. Live Data

The system can operate in two modes:

1. **Live Data Mode**: Uses real-time market data from Alpaca API
2. **Simulation Mode**: Uses simulated market data for testing

To switch between modes, change the `use_simulation` flag in the initial state in `main.py`:

```python
# Use simulated data (when APIs are down)
inputs = {
    # ... other inputs ...
    "use_simulation": True
}

# Use real Alpaca API data (when APIs are working)
inputs = {
    # ... other inputs ...
    "use_simulation": False
}
```

## System Architecture

The system is built using LangGraph, which allows for creating complex workflows with specialized agents. Each agent has a specific role in the trading process:

- **User Interface Agent**: Handles user input and presents results
- **Strategy Agent**: Uses LLM to convert natural language to structured trading rules
- **Market Data Agent**: Fetches and processes market data from various sources
- **Trading Logic Agent**: Analyzes market data against strategy rules
- **Portfolio Management Agent**: Manages portfolio and executes trades

## Checkpoints & Known Issues

### Implemented Checkpoints

- [x] User interface for strategy input
- [x] Strategy interpretation into structured JSON
- [x] Market data simulation when APIs are unavailable
- [x] Basic portfolio management and trade execution
- [x] Continuous market watching with simulated price updates

### Pending Checkpoints

- [ ] Implement proper error handling for API failures
- [ ] Add visualization of portfolio performance over time
- [ ] Support for more complex strategy types (e.g., multi-asset strategies)
- [ ] Implement strategy testing with historical data
- [ ] Add risk management rules and position sizing
- [ ] Create a web interface for easier interaction

### Known Issues

- **Market Watching Loop**: Currently, the system may exit prematurely if certain conditions aren't met instead of continuing to watch the market. This needs to be fixed by improving the conditional logic in the `should_continue_watching` function to properly wait until strategy conditions are met.
- **API Dependencies**: External API connections (Alpaca) may fail, requiring the use of simulated data mode.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
