import yfinance as yf, json, time, pandas as pd
from datetime import datetime, timezone

SIGNAL_FILE  = '/root/gold_signal.json'
HISTORY_FILE = '/home/andre/logs/signal_history.jsonl'

print(f"[{datetime.now(timezone.utc)}] Gold Bot started", flush=True)

while True:
    try:
        gold = yf.download('GC=F', period='3mo', progress=False, timeout=30)
        if isinstance(gold.columns, pd.MultiIndex):
            gold.columns = gold.columns.get_level_values(0)

        close = gold['Close']
        price  = float(close.iloc[-1])
        prev   = float(close.iloc[-2])
        change = round((price - prev) / prev * 100, 2)

        # Moving averages
        ma20 = float(close.rolling(20).mean().iloc[-1]) if len(gold) >= 20 else price
        ma50 = float(close.rolling(50).mean().iloc[-1]) if len(gold) >= 50 else price

        # RSI(14)
        delta = close.diff()
        gain  = delta.where(delta > 0, 0).rolling(14).mean()
        loss  = -delta.where(delta < 0, 0).rolling(14).mean()
        rs    = gain.iloc[-1] / loss.iloc[-1] if loss.iloc[-1] != 0 else 99
        rsi   = float(100 - 100 / (1 + rs))

        # MACD(12,26,9)
        ema12       = close.ewm(span=12, adjust=False).mean()
        ema26       = close.ewm(span=26, adjust=False).mean()
        macd_line   = ema12 - ema26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        macd        = float(macd_line.iloc[-1])
        macd_sig    = float(signal_line.iloc[-1])
        macd_hist   = float((macd_line - signal_line).iloc[-1])

        # Bollinger Bands(20,2)
        bb_mid   = close.rolling(20).mean()
        bb_std   = close.rolling(20).std()
        bb_upper = float((bb_mid + 2 * bb_std).iloc[-1])
        bb_lower = float((bb_mid - 2 * bb_std).iloc[-1])
        bb_mid_v = float(bb_mid.iloc[-1])
        bb_pos   = (price - bb_lower) / (bb_upper - bb_lower) if (bb_upper - bb_lower) > 0 else 0.5

        # Signal scoring across 5 indicators
        b, s = 0, 0
        if price > ma20:        b += 1
        else:                   s += 1
        if ma20 > ma50:         b += 1
        else:                   s += 1
        if rsi > 55:            b += 1
        elif rsi < 45:          s += 1
        if macd > macd_sig:     b += 1
        else:                   s += 1
        if price <= bb_lower:   b += 1
        elif price >= bb_upper: s += 1

        if   b >= 4: sig = "STRONG BUY"
        elif b >= 3: sig = "BUY"
        elif s >= 4: sig = "STRONG SELL"
        elif s >= 3: sig = "SELL"
        else:        sig = "HOLD"

        now = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')

        data = {
            'price': round(price, 2), 'change': change,
            'rsi': round(rsi, 1),
            'ma20': round(ma20, 2), 'ma50': round(ma50, 2),
            'macd': round(macd, 2), 'macd_signal': round(macd_sig, 2), 'macd_hist': round(macd_hist, 2),
            'bb_upper': round(bb_upper, 2), 'bb_mid': round(bb_mid_v, 2), 'bb_lower': round(bb_lower, 2),
            'bb_pos': round(bb_pos, 3),
            'signal': sig, 'time': now
        }

        with open(SIGNAL_FILE, 'w') as f:
            json.dump(data, f)
        with open(HISTORY_FILE, 'a') as f:
            f.write(json.dumps(data) + '\n')

        print(f"[{now}] ${price:,.2f} | RSI {rsi:.1f} | MACD {macd_hist:+.2f} | BB {bb_pos:.0%} | {sig}", flush=True)
        time.sleep(300)
    except Exception as e:
        print(f"Error: {e}", flush=True)
        time.sleep(60)
