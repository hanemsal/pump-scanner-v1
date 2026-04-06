from fastapi import FastAPI
from simulator.signal_simulator import simulate_signal

app = FastAPI()

@app.get("/signals")

def signals():
    return simulate_signal()
