# scripts

Personal automation scripts running on my home server.

## Contents

### `gold_bot.py`
Monitors gold futures (`GC=F`) every 5 minutes using `yfinance`. Calculates RSI, 20-day and 50-day moving averages, and writes a trading signal (`STRONG BUY` / `BUY` / `HOLD` / `SELL` / `STRONG SELL`) to `/root/gold_signal.json`.

### `start_all_services.sh`
Starts all home server services:

| Service | Port | Description |
|---|---|---|
| OpenJarvis API | 8080 | AI assistant backend |
| Jarvis Frontend | 5000 | Chat UI |
| Gold Dashboard | 8050 | Gold bot signal viewer |
| Gold Bot | — | Background signal generator |

## Requirements

```bash
pip install yfinance pandas
```
