import yfinance as yf, json, time, pandas as pd, sys
from datetime import datetime, timezone

print(f"[{datetime.now(timezone.utc)}] 🥇 Gold Bot started", flush=True)

while True:
    try:
        gold = yf.download('GC=F', period='3mo', progress=False, timeout=30)
        if isinstance(gold.columns, pd.MultiIndex):
            gold.columns = gold.columns.get_level_values(0)
        price = float(gold['Close'].iloc[-1])
        prev = float(gold['Close'].iloc[-2])
        change = round((price - prev) / prev * 100, 2)
        ma20 = float(gold['Close'].rolling(20).mean().iloc[-1]) if len(gold)>=20 else price
        ma50 = float(gold['Close'].rolling(50).mean().iloc[-1]) if len(gold)>=50 else price

        # Simple RSI
        delta = gold['Close'].diff()
        gain = delta.where(delta>0,0).rolling(14).mean()
        loss = -delta.where(delta<0,0).rolling(14).mean()
        rsi = float(100 - (100/(1+gain/loss)).iloc[-1]) if not (gain.iloc[-1]==0 and loss.iloc[-1]==0) else 50

        # Signal
        if price > ma20 > ma50 and rsi > 50:
            signal = "STRONG BUY"
        elif price > ma20:
            signal = "BUY"
        elif price < ma20 < ma50 and rsi < 50:
            signal = "STRONG SELL"
        elif price < ma20:
            signal = "SELL"
        else:
            signal = "HOLD"

        data = {
            'price': round(price,2),
            'change': change,
            'rsi': round(rsi,1) if rsi == rsi else None,
            'ma20': round(ma20,2),
            'ma50': round(ma50,2),
            'signal': signal,
            'time': datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
        }
        with open('/root/gold_signal.json','w') as f:
            json.dump(data, f)

        print(f"[{data['time']}] Gold ${price:,.2f} | RSI {rsi:.1f} | {signal}", flush=True)
        time.sleep(300)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(60)
