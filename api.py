import os
from fastapi import FastAPI
from binance.client import Client
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="RSI Bot API")

# Binance Testnet istemcisi
client = Client(os.getenv("BINANCE_API_KEY"), os.getenv("BINANCE_SECRET_KEY"), testnet=True)

@app.get("/")
def home():
    return {"status": "Bot API Calisiyor"}

@app.get("/bakiye")
def get_bakiye():
    """Testnet üzerindeki toplam USDT bakiyesini döner"""
    try:
        balance = client.get_asset_balance(asset='USDT')
        return {"usdt_free": balance['free'], "usdt_locked": balance['locked']}
    except Exception as e:
        return {"error": str(e)}

@app.get("/pozisyonlar")
def get_pozisyonlar():
    """Açık pozisyonları ve bakiyeleri döner"""
    try:
        account = client.get_account()
        active_assets = []
        for asset in account['balances']:
            free = float(asset['free'])
            locked = float(asset['locked'])
            if (free > 0 or locked > 0) and asset['asset'] != 'USDT':
                active_assets.append({
                    "symbol": asset['asset'],
                    "free": free,
                    "locked": locked
                })
        return {"pozisyonlar": active_assets}
    except Exception as e:
        return {"error": str(e)}