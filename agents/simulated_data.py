"""
Simulated market data generator for testing the trading system.
This module provides functions to generate realistic-looking market data
without requiring external API connections.
"""

import random
from datetime import datetime, timedelta

def generate_simulated_data():
    """Generate simulated market data for testing purposes."""
    print("Generating simulated market data...")
    
    # Define the symbols we want to simulate
    symbols_to_simulate = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "SPY"]
    
    # Create a dictionary to hold our simulated data
    simulated_data = {}
    
    # Generate some realistic price data for each symbol
    base_prices = {
        "AAPL": 175.0,
        "GOOGL": 140.0,
        "MSFT": 380.0,
        "AMZN": 180.0,
        "TSLA": 250.0,
        "SPY": 500.0
    }
    
    # Generate historical bars data
    historical_bars = {}
    for symbol in symbols_to_simulate:
        base_price = base_prices.get(symbol, 100.0)
        # Generate 30 days of data with some random variation
        bars = []
        for i in range(30):
            # Add some random variation to create realistic looking data
            variation = (0.5 - random.random()) * 5  # Random between -2.5% and +2.5%
            price = base_price * (1 + variation/100)
            
            # Create a bar record
            bar = {
                "timestamp": (datetime.now() - timedelta(days=30-i)).isoformat(),
                "open": price * 0.99,
                "high": price * 1.02,
                "low": price * 0.98,
                "close": price,
                "volume": random.randint(1000000, 10000000)
            }
            bars.append(bar)
        
        historical_bars[symbol] = bars
    
    simulated_data["historical_bars"] = historical_bars
    
    # Generate some quote data
    quotes = []
    for symbol in symbols_to_simulate:
        base_price = base_prices.get(symbol, 100.0)
        # Add some random variation
        bid_price = base_price * 0.999  # Slightly lower than base
        ask_price = base_price * 1.001  # Slightly higher than base
        
        quote = {
            "symbol": symbol,
            "bid_price": bid_price,
            "ask_price": ask_price,
            "bid_size": random.randint(100, 1000),
            "ask_size": random.randint(100, 1000),
            "timestamp": datetime.now().isoformat()
        }
        quotes.append(quote)
    
    simulated_data["quote"] = quotes
    
    # Generate some trade data
    trades = []
    for symbol in symbols_to_simulate:
        base_price = base_prices.get(symbol, 100.0)
        
        trade = {
            "symbol": symbol,
            "price": base_price,
            "size": random.randint(100, 1000),
            "timestamp": datetime.now().isoformat()
        }
        trades.append(trade)
    
    simulated_data["trade"] = trades
    
    # Generate some bar data (current day)
    bars = []
    for symbol in symbols_to_simulate:
        base_price = base_prices.get(symbol, 100.0)
        
        bar = {
            "symbol": symbol,
            "open": base_price * 0.99,
            "high": base_price * 1.02,
            "low": base_price * 0.98,
            "close": base_price,
            "volume": random.randint(1000000, 5000000),
            "timestamp": datetime.now().isoformat()
        }
        bars.append(bar)
    
    simulated_data["bar"] = bars
    
    print(f"Generated simulated data for {len(symbols_to_simulate)} symbols")
    return simulated_data

def generate_price_update(symbol, current_price=None):
    """Generate a simulated price update for a given symbol."""
    if current_price is None:
        # Use default base prices if no current price is provided
        base_prices = {
            "AAPL": 175.0,
            "GOOGL": 140.0,
            "MSFT": 380.0,
            "AMZN": 180.0,
            "TSLA": 250.0,
            "SPY": 500.0
        }
        current_price = base_prices.get(symbol, 100.0)
    
    # Add some random variation to create realistic price movement
    variation = (0.5 - random.random()) * 0.5  # Random between -0.25% and +0.25%
    new_price = current_price * (1 + variation/100)
    
    return {
        "symbol": symbol,
        "price": new_price,
        "timestamp": datetime.now().isoformat()
    }
