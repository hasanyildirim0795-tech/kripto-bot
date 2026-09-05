import os
import time
import ccxt
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv

# .env dosyasını yükle
load_dotenv()

api_key = os.getenv('BINANCE_API_KEY')
secret_key = os.getenv('BINANCE_SECRET_KEY')

# Binance Testnet Bağlantısı
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': secret_key,
    'enableRateLimit': True,
    'options': {'defaultType': 'spot'}
})
exchange.set_sandbox_mode(True)

# Risk ve Strateji Parametreleri
TRADE_AMOUNT_USDT = 500     # İşlem başına 500 USDT
TAKE_PROFIT_PERCENT = 0.02  # %2.0 Kar Al
STOP_LOSS_PERCENT = 0.01   # %1.0 Zarar Durdur
MAX_OPEN_POSITIONS = 5     # Aynı anda açılabilecek maksimum farklı coin pozisyonu

# Aktif Pozisyonlar Sözlüğü
active_positions = {}

def get_tradable_symbols():
    """Hacmi yüksek aktif USDT işlem çiftlerini getirir."""
    try:
        tickers = exchange.fetch_tickers()
        valid_symbols = []
        for symbol, ticker in tickers.items():
            if symbol.endswith('/USDT') and ticker.get('quoteVolume') and ticker['quoteVolume'] > 50000:
                valid_symbols.append(symbol)
        return valid_symbols[:30]
    except Exception:
        return ['BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'BNB/USDT', 'XRP/USDT']

print("Çoklu Pozisyon Destekli Bot Başlatıldı (500 USDT / İşlem)...\n")

while True:
    try:
        # 1. ADIM: AÇIK POZİSYONLARIN TAKİBİ
        for symbol in list(active_positions.keys()):
            try:
                pos = active_positions[symbol]
                ticker = exchange.fetch_ticker(symbol)
                current_price = float(ticker['last'])
                
                entry_price = pos['entry_price']
                tp_price = entry_price * (1 + TAKE_PROFIT_PERCENT)
                sl_price = entry_price * (1 - STOP_LOSS_PERCENT)
                
                print(f"[AÇIK POZİSYON] {symbol} | Anlık: {current_price:.4f} | TP: {tp_price:.4f} | SL: {sl_price:.4f}")
                
                if current_price >= tp_price or current_price <= sl_price:
                    balance = exchange.fetch_balance()
                    base_currency = symbol.split('/')[0]
                    sell_amount = float(balance['free'].get(base_currency, 0))
                    
                    if sell_amount > 0:
                        exchange.create_market_sell_order(symbol, sell_amount)
                        profit_loss = ((current_price - entry_price) / entry_price) * 100
                        print(f"--> [SATIŞ YAPILDI] {symbol} kapatıldı. Sonuc: %{profit_loss:.2f}\n")
                    
                    del active_positions[symbol]
                    
            except Exception as err:
                print(f"{symbol} pozisyon takibinde hata: {err}")

        # 2. ADIM: YENİ FIRSATLARI TARAMA
        if len(active_positions) < MAX_OPEN_POSITIONS:
            symbols = get_tradable_symbols()
            
            for symbol in symbols:
                if len(active_positions) >= MAX_OPEN_POSITIONS:
                    break
                if symbol in active_positions:
                    continue
                
                try:
                    calc_amount = 0.0  # Değişken önceden tanımlandı (Pylance uyarısını çözer)
                    
                    bars = exchange.fetch_ohlcv(symbol, timeframe='1m', limit=50)
                    df = pd.DataFrame(bars, columns=['time', 'open', 'high', 'low', 'close', 'volume'])
                    
                    rsi_series = ta.rsi(df['close'], length=14)
                    if isinstance(rsi_series, pd.DataFrame):
                        rsi_series = rsi_series.iloc[:, 0]
                        
                    last_price = float(df['close'].iloc[-1])
                    last_rsi = float(rsi_series.iloc[-1])
                    
                    print(f"Tarama: {symbol:<10} | Fiyat: {last_price:<10.4f} | RSI: {last_rsi:.2f}")
                    
                    # Alım Sinyali Kontrolü (RSI < 35)
                    if last_rsi < 35:
                        calc_amount = TRADE_AMOUNT_USDT / last_price
                        exchange.create_market_buy_order(symbol, calc_amount)
                        
                        active_positions[symbol] = {
                            'entry_price': last_price,
                            'amount': calc_amount
                        }
                        
                        print(f"\n--> [ALIM YAPILDI] Sembol: {symbol} | Fiyat: {last_price} | Tutar: {TRADE_AMOUNT_USDT} USDT\n")
                        
                except Exception:
                    pass
                
                time.sleep(0.2)

        time.sleep(3)

    except Exception as e:
        print(f"Genel Hata: {e}")
        time.sleep(5)