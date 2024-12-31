import requests
import numpy as np
import pandas as pd
import aiohttp
import asyncio
import talib
import datetime
import matplotlib.pyplot as plt

# Récupération des données historiques pour les cryptomonnaies
async def fetch_historical_data(crypto_symbol, currency="USD", interval="day", limit=2000):
    base_url = "https://min-api.cryptocompare.com/data/v2/"
    endpoint = "histoday"  # Utiliser des données journalières pour le backtest
    url = f"{base_url}{endpoint}"
    params = {
        "fsym": crypto_symbol.upper(),
        "tsym": currency.upper(),
        "limit": limit,
        "api_key": "70001b698e6a3d349e68ba1b03e7489153644e38c5026b4a33d55c8e460c7a3c"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as response:
            response.raise_for_status()
            data = await response.json()

    if data.get("Response") == "Success" and "Data" in data:
        prices = []
        for item in data["Data"].get("Data", []):
            if all(key in item for key in ["time", "open", "high", "low", "close", "volumeto"]):
                prices.append({
                    "time": datetime.datetime.fromtimestamp(item["time"]),
                    "open": item["open"],
                    "high": item["high"],
                    "low": item["low"],
                    "close": item["close"],
                    "volume": item["volumeto"]
                })
        return prices
    else:
        print(f"Erreur API : {data.get('Message', 'Données invalides.')}")
        return []

# Fonction de calcul des indicateurs avec TA-Lib
def calculate_indicators(prices):
    closes = np.array([price["close"] for price in prices])
    highs = np.array([price["high"] for price in prices])
    lows = np.array([price["low"] for price in prices])

    sma_short = talib.SMA(closes, timeperiod=10)
    sma_long = talib.SMA(closes, timeperiod=50)
    ema_short = talib.EMA(closes, timeperiod=12)
    ema_long = talib.EMA(closes, timeperiod=26)
    macd, macd_signal, macd_hist = talib.MACD(closes, fastperiod=12, slowperiod=26, signalperiod=9)
    atr = talib.ATR(highs, lows, closes, timeperiod=14)
    rsi = talib.RSI(closes, timeperiod=14)
    slowk, slowd = talib.STOCH(highs, lows, closes, fastk_period=14, slowk_period=3, slowd_period=3)
    adx = talib.ADX(highs, lows, closes, timeperiod=14)

    return {
        "SMA_short": sma_short,
        "SMA_long": sma_long,
        "EMA_short": ema_short,
        "EMA_long": ema_long,
        "MACD": macd,
        "ATR": atr,
        "RSI": rsi,
        "Stochastic_K": slowk,
        "Stochastic_D": slowd,
        "ADX": adx
    }

# Analyser les signaux de trading
def analyze_signals(indicators, index):
    if indicators['RSI'][index] < 30 and indicators['Stochastic_K'][index] < 20 and indicators['ADX'][index] > 20 and indicators['EMA_short'][index] > indicators['EMA_long'][index]:
        return "Acheter"
    elif indicators['RSI'][index] > 70 and indicators['Stochastic_K'][index] > 80 and indicators['ADX'][index] > 20 and indicators['EMA_short'][index] < indicators['EMA_long'][index]:
        return "Vendre"
    elif indicators['MACD'][index] > 0 and indicators['EMA_short'][index] > indicators['EMA_long'][index] and indicators['ADX'][index] > 20:
        return "Acheter"
    elif indicators['MACD'][index] < 0 and indicators['EMA_short'][index] < indicators['EMA_long'][index] and indicators['ADX'][index] > 20:
        return "Vendre"
    else:
        return "Ne rien faire"

# Simuler les transactions
def backtest(prices, initial_capital=10000):
    indicators = calculate_indicators(prices)
    capital = initial_capital
    position = 0
    capital_history = []

    for i in range(len(prices)):
        signal = analyze_signals(indicators, i)
        if signal == "Acheter" and capital > 0:
            position = capital / prices[i]["close"]
            capital = 0
            print(f"Achat à {prices[i]['close']} le {prices[i]['time']}")
        elif signal == "Vendre" and position > 0:
            capital = position * prices[i]["close"]
            position = 0
            print(f"Vente à {prices[i]['close']} le {prices[i]['time']}")
        capital_history.append(capital + position * prices[i]["close"])

    return capital_history

# Récupérer les données historiques et effectuer le backtest
async def main():
    crypto_symbol = "BTC"
    prices = await fetch_historical_data(crypto_symbol)
    if prices:
        capital_history = backtest(prices)
        # Afficher les résultats du backtest
        df = pd.DataFrame({"Date": [price["time"] for price in prices], "Capital": capital_history})
        df.set_index("Date", inplace=True)
        df.plot(title="Backtest Capital Over Time", figsize=(10, 6))
        plt.show()

if __name__ == "__main__":
    asyncio.run(main())
