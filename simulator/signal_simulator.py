import random

def simulate_signal():

    coins = ["BTC","ETH","SOL","ARB","DOGE"]

    coin = random.choice(coins)

    return {
        "symbol": coin,
        "entry": random.uniform(0.1,1),
        "tp": "x5",
        "sl": "x1"
    }

print(simulate_signal())
