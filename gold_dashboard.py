from flask import Flask, jsonify, render_template_string
import json, subprocess, pandas as pd
from datetime import datetime
import yfinance as yf

app = Flask(__name__)

SIGNAL_FILE  = '/root/gold_signal.json'
HISTORY_FILE = '/home/andre/logs/signal_history.jsonl'
LOG_FILE     = '/home/andre/logs/gold_bot.log'

HTML = '''<!DOCTYPE html>
<html>
<head>
    <title>Gold Trading Bot</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
    <style>
        * { margin:0; padding:0; box-sizing:border-box; }
        body {
            font-family: 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #0d1117 0%, #161b22 100%);
            min-height: 100vh; color: #e6edf3; padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header {
            background: linear-gradient(135deg, #b8860b, #ffd700, #ff8c00);
            border-radius: 16px; padding: 28px; margin-bottom: 24px;
            text-align: center; box-shadow: 0 8px 32px rgba(255,215,0,0.25);
        }
        .header h1 { font-size: 2.4em; color: #0d1117; font-weight: 800; }
        .header p  { color: #1a1a2e; font-size: 1.05em; margin-top: 6px; }
        .tab-nav { display:flex; justify-content:center; gap:12px; margin-bottom:24px; }
        .tab-btn {
            background: rgba(255,255,255,0.06); color: #ffd700;
            border: 2px solid #ffd700; padding: 10px 28px;
            border-radius: 24px; cursor: pointer; font-size: 0.95em;
            font-weight: 600; transition: 0.2s;
        }
        .tab-btn.active, .tab-btn:hover {
            background: linear-gradient(135deg,#b8860b,#ffd700);
            color: #0d1117; border-color: #ffd700;
        }
        .cards { display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:16px; margin-bottom:20px; }
        .card {
            background: rgba(255,255,255,0.05); backdrop-filter:blur(8px);
            border-radius:16px; padding:24px;
            border: 1px solid rgba(255,255,255,0.1); transition: transform 0.2s;
        }
        .card:hover { transform:translateY(-3px); }
        .card-label { font-size:0.8em; text-transform:uppercase; letter-spacing:2px; color:#8b949e; margin-bottom:8px; }
        .card-value { font-size:2.2em; font-weight:700; margin:8px 0; }
        .card-sub   { font-size:0.85em; color:#8b949e; }
        .signal-STRONG\\ BUY, .signal-BUY  { color:#3fb950; }
        .signal-STRONG\\ SELL,.signal-SELL { color:#f85149; }
        .signal-HOLD { color:#ffd700; }
        .up   { color:#3fb950; }
        .down { color:#f85149; }
        .chart-card {
            background: rgba(255,255,255,0.05); border-radius:16px;
            padding:20px; margin-bottom:20px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .chart-card h3 { color:#ffd700; margin-bottom:16px; font-size:1.05em; }
        #chart { width:100%; height:460px; }
        #chart-loading { text-align:center; padding:80px; color:#8b949e; font-size:1.1em; }
        .two-col { display:grid; grid-template-columns:1fr 1fr; gap:16px; margin-bottom:20px; }
        @media(max-width:900px){ .two-col { grid-template-columns:1fr; } }
        .tech-row { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid rgba(255,255,255,0.07); }
        .tech-row:last-child { border-bottom:none; }
        .tech-label { color:#8b949e; font-size:0.9em; }
        .tech-value { font-weight:600; font-size:0.95em; }
        .badge { padding:3px 10px; border-radius:12px; font-size:0.8em; font-weight:600; }
        .badge-bull { background:rgba(63,185,80,0.2); color:#3fb950; }
        .badge-bear { background:rgba(248,81,73,0.2); color:#f85149; }
        .badge-neut { background:rgba(255,215,0,0.2); color:#ffd700; }
        table { width:100%; border-collapse:collapse; font-size:0.88em; }
        th { color:#8b949e; font-weight:600; text-align:left; padding:8px 10px; border-bottom:1px solid rgba(255,255,255,0.1); }
        td { padding:8px 10px; border-bottom:1px solid rgba(255,255,255,0.05); }
        tr:last-child td { border-bottom:none; }
        .log-box {
            background:#0d1117; border-radius:10px; padding:16px;
            font-family:'Courier New',monospace; max-height:220px;
            overflow-y:auto; font-size:0.82em; color:#3fb950; line-height:1.6;
        }
        .mini-grid { display:grid; grid-template-columns:repeat(auto-fill,minmax(180px,1fr)); gap:12px; }
        .mini-card {
            background:rgba(255,255,255,0.05); border-radius:12px; padding:16px;
            text-align:center; border:1px solid rgba(255,255,255,0.08); transition:0.2s;
        }
        .mini-card:hover { border-color:#ffd700; }
        .mini-name  { color:#ffd700; font-weight:600; margin-bottom:6px; font-size:0.9em; }
        .mini-price { font-size:1.2em; font-weight:700; }
        .mini-chg   { font-size:0.85em; margin-top:4px; }
        .refresh-btn {
            background:linear-gradient(135deg,#b8860b,#ffd700);
            color:#0d1117; border:none; padding:10px 28px;
            border-radius:24px; cursor:pointer; font-size:0.9em; font-weight:700;
        }
        #last-update { color:#8b949e; font-size:0.85em; margin-left:16px; }
    </style>
</head>
<body>
<div class="container">
    <div class="header">
        <h1>🥇 Gold Trading Bot</h1>
        <p>Live technical analysis · Updated every 5 minutes</p>
    </div>

    <div class="tab-nav">
        <button class="tab-btn active" onclick="switchTab('gold')">🥇 Gold Analysis</button>
        <button class="tab-btn" onclick="switchTab('markets')">🌍 Global Markets</button>
    </div>

    <!-- GOLD ANALYSIS TAB -->
    <div id="tab-gold">
        <div style="text-align:center;margin-bottom:20px;">
            <button class="refresh-btn" onclick="loadGold()">↻ Refresh</button>
            <span id="last-update"></span>
        </div>

        <!-- Metric cards -->
        <div class="cards">
            <div class="card">
                <div class="card-label">💰 Gold Price</div>
                <div class="card-value" style="color:#ffd700;" id="c-price">—</div>
                <div class="card-sub" id="c-change">USD per oz</div>
            </div>
            <div class="card">
                <div class="card-label">🎯 Signal</div>
                <div class="card-value" id="c-signal">—</div>
                <div class="card-sub" id="c-time"></div>
            </div>
            <div class="card">
                <div class="card-label">📈 RSI (14)</div>
                <div class="card-value" style="color:#58a6ff;" id="c-rsi">—</div>
                <div class="card-sub" id="c-rsi-zone"></div>
            </div>
            <div class="card">
                <div class="card-label">⚡ MACD Histogram</div>
                <div class="card-value" id="c-macd-hist">—</div>
                <div class="card-sub" id="c-macd-cross"></div>
            </div>
        </div>

        <!-- Price chart -->
        <div class="chart-card">
            <h3>📊 Price Chart — 3 Months  <span style="font-size:0.8em;color:#8b949e;font-weight:400;">MA20 · MA50 · Bollinger Bands · Signals</span></h3>
            <div id="chart-loading">Loading chart data…</div>
            <div id="chart" style="display:none;"></div>
        </div>

        <!-- Technical summary + signal history -->
        <div class="two-col">
            <div class="card">
                <h3 style="color:#ffd700;margin-bottom:16px;">🔬 Technical Summary</h3>
                <div id="tech-summary"></div>
            </div>
            <div class="card">
                <h3 style="color:#ffd700;margin-bottom:16px;">📋 Signal History</h3>
                <div id="sig-history" style="overflow-x:auto;"></div>
            </div>
        </div>

        <!-- Live logs -->
        <div class="chart-card">
            <h3>📝 Live Bot Logs</h3>
            <div class="log-box" id="logs">Loading…</div>
        </div>
    </div>

    <!-- GLOBAL MARKETS TAB -->
    <div id="tab-markets" style="display:none;">
        <div style="text-align:center;margin-bottom:20px;">
            <button class="refresh-btn" onclick="loadMarkets()">↻ Refresh Markets</button>
        </div>
        <div class="mini-grid" id="markets-grid"><p style="color:#8b949e;text-align:center;padding:40px;">Loading…</p></div>
    </div>
</div>

<script>
function switchTab(t) {
    document.getElementById('tab-gold').style.display    = t==='gold'    ? 'block' : 'none';
    document.getElementById('tab-markets').style.display = t==='markets' ? 'block' : 'none';
    document.querySelectorAll('.tab-btn').forEach((b,i) => b.classList.toggle('active', (t==='gold'&&i===0)||(t==='markets'&&i===1)));
    if (t==='markets') loadMarkets();
}

function rsiZone(v) {
    if (v >= 70) return ['Overbought','bear'];
    if (v <= 30) return ['Oversold','bull'];
    if (v >= 55) return ['Bullish','bull'];
    if (v <= 45) return ['Bearish','bear'];
    return ['Neutral','neut'];
}

function badge(label, type) {
    return `<span class="badge badge-${type}">${label}</span>`;
}

function loadGold() {
    fetch('/api/gold_data').then(r=>r.json()).then(d => {
        const chgSign = d.change >= 0 ? '+' : '';
        const chgCls  = d.change >= 0 ? 'up' : 'down';
        document.getElementById('c-price').textContent  = '$' + d.price;
        document.getElementById('c-change').innerHTML   = `<span class="${chgCls}">${chgSign}${d.change}%</span> today`;
        const sig = document.getElementById('c-signal');
        sig.textContent  = d.signal;
        sig.className    = 'card-value signal-' + d.signal.replace(/ /g,'_');
        document.getElementById('c-time').textContent   = d.time;
        document.getElementById('c-rsi').textContent    = d.rsi;
        const [rzone, rcls] = rsiZone(d.rsi);
        document.getElementById('c-rsi-zone').innerHTML = badge(rzone, rcls);
        const hCls = d.macd_hist >= 0 ? 'up' : 'down';
        document.getElementById('c-macd-hist').innerHTML = `<span class="${hCls}">${d.macd_hist >= 0 ? '+' : ''}${d.macd_hist}</span>`;
        document.getElementById('c-macd-cross').innerHTML = d.macd > d.macd_signal ? badge('Bullish crossover','bull') : badge('Bearish crossover','bear');
        document.getElementById('last-update').textContent = 'Updated ' + new Date().toLocaleTimeString();

        // Technical summary
        const bbPos = Math.round(d.bb_pos * 100);
        const trendBull = d.price > d.ma20 && d.ma20 > d.ma50;
        const trendBear = d.price < d.ma20 && d.ma20 < d.ma50;
        document.getElementById('tech-summary').innerHTML = `
            <div class="tech-row"><span class="tech-label">Price vs MA20</span><span class="tech-value">${d.price > d.ma20 ? badge('Above','bull') : badge('Below','bear')} $${d.ma20}</span></div>
            <div class="tech-row"><span class="tech-label">Price vs MA50</span><span class="tech-value">${d.price > d.ma50 ? badge('Above','bull') : badge('Below','bear')} $${d.ma50}</span></div>
            <div class="tech-row"><span class="tech-label">MA Trend</span><span class="tech-value">${trendBull ? badge('Uptrend','bull') : trendBear ? badge('Downtrend','bear') : badge('Mixed','neut')}</span></div>
            <div class="tech-row"><span class="tech-label">RSI (14)</span><span class="tech-value">${badge(rzone, rcls)} ${d.rsi}</span></div>
            <div class="tech-row"><span class="tech-label">MACD</span><span class="tech-value">${d.macd > d.macd_signal ? badge('Bullish','bull') : badge('Bearish','bear')} ${d.macd} / ${d.macd_signal}</span></div>
            <div class="tech-row"><span class="tech-label">Bollinger Position</span><span class="tech-value">${bbPos}% <span style="color:#8b949e;font-size:0.85em;">(${d.bb_lower} – ${d.bb_upper})</span></span></div>
        `;
    });

    fetch('/api/logs').then(r=>r.text()).then(t => {
        const el = document.getElementById('logs');
        el.textContent = t;
        el.scrollTop   = el.scrollHeight;
    });

    fetch('/api/signal_history').then(r=>r.json()).then(rows => {
        if (!rows.length) { document.getElementById('sig-history').innerHTML='<p style="color:#8b949e;padding:20px 0;">No history yet — check back in a few minutes.</p>'; return; }
        let html = '<table><thead><tr><th>Time</th><th>Price</th><th>Signal</th><th>Change</th></tr></thead><tbody>';
        rows.forEach(r => {
            const cls  = r.signal.includes('BUY') ? 'up' : r.signal.includes('SELL') ? 'down' : '';
            const sign = r.since >= 0 ? '+' : '';
            const sinceStr = r.since !== null ? `<span class="${r.since>=0?'up':'down'}">${sign}${r.since}%</span>` : '—';
            html += `<tr><td style="color:#8b949e">${r.time}</td><td>$${r.price.toLocaleString()}</td><td class="${cls}" style="font-weight:600">${r.signal}</td><td>${sinceStr}</td></tr>`;
        });
        html += '</tbody></table>';
        document.getElementById('sig-history').innerHTML = html;
    });
}

function loadChart() {
    fetch('/api/chart_data').then(r=>r.json()).then(d => {
        document.getElementById('chart-loading').style.display = 'none';
        document.getElementById('chart').style.display = 'block';

        const traces = [
            // Bollinger band fill
            { x:d.dates, y:d.bb_upper, name:'BB Upper', line:{color:'rgba(88,166,255,0.3)',width:1}, showlegend:false },
            { x:d.dates, y:d.bb_lower, name:'BB Lower', fill:'tonexty', fillcolor:'rgba(88,166,255,0.08)', line:{color:'rgba(88,166,255,0.3)',width:1}, showlegend:false },
            // MAs
            { x:d.dates, y:d.ma50, name:'MA50', line:{color:'#f85149',width:1.5,dash:'dot'} },
            { x:d.dates, y:d.ma20, name:'MA20', line:{color:'#58a6ff',width:1.5,dash:'dot'} },
            // Price
            { x:d.dates, y:d.prices, name:'Gold', line:{color:'#ffd700',width:2.5} },
        ];

        // Signal markers
        const buyDates=[], buyPrices=[], buyText=[];
        const sellDates=[], sellPrices=[], sellText=[];
        (d.signals||[]).forEach(s => {
            if (s.signal.includes('BUY'))  { buyDates.push(s.time);  buyPrices.push(s.price);  buyText.push(s.signal); }
            if (s.signal.includes('SELL')) { sellDates.push(s.time); sellPrices.push(s.price); sellText.push(s.signal); }
        });
        if (buyDates.length)  traces.push({ x:buyDates,  y:buyPrices,  mode:'markers', name:'Buy Signal',  text:buyText,  marker:{symbol:'triangle-up',  size:10, color:'#3fb950'} });
        if (sellDates.length) traces.push({ x:sellDates, y:sellPrices, mode:'markers', name:'Sell Signal', text:sellText, marker:{symbol:'triangle-down', size:10, color:'#f85149'} });

        Plotly.newPlot('chart', traces, {
            paper_bgcolor:'transparent', plot_bgcolor:'rgba(255,255,255,0.02)',
            font:{color:'#e6edf3', size:12},
            xaxis:{gridcolor:'rgba(255,255,255,0.06)', tickfont:{size:11}},
            yaxis:{gridcolor:'rgba(255,255,255,0.06)', tickprefix:'$', tickformat:',.0f'},
            legend:{bgcolor:'rgba(0,0,0,0.3)', bordercolor:'rgba(255,255,255,0.1)', borderwidth:1},
            margin:{t:20,r:20,b:40,l:70}, hovermode:'x unified',
            hoverlabel:{bgcolor:'#161b22', bordercolor:'#ffd700', font:{color:'#e6edf3'}}
        }, {responsive:true, displayModeBar:false});
    });
}

function loadMarkets() {
    document.getElementById('markets-grid').innerHTML = '<p style="color:#8b949e;text-align:center;padding:40px;">Loading…</p>';
    fetch('/api/markets_overview').then(r=>r.json()).then(data => {
        const html = data.map(item => {
            const cls  = item.change >= 0 ? 'up' : 'down';
            const sign = item.change >= 0 ? '+' : '';
            return `<div class="mini-card">
                <div class="mini-name">${item.market}</div>
                <div class="mini-price">${item.price}</div>
                <div class="mini-chg ${cls}">${sign}${item.change}%</div>
            </div>`;
        }).join('');
        document.getElementById('markets-grid').innerHTML = html || '<p style="color:#8b949e;text-align:center;padding:40px;">No data available</p>';
    });
}

// Init
loadGold();
loadChart();
setInterval(loadGold, 300000);
</script>
</body>
</html>'''


@app.route('/')
def home():
    return render_template_string(HTML)


@app.route('/api/gold_data')
def gold_data():
    try:
        with open(SIGNAL_FILE) as f:
            d = json.load(f)
    except Exception:
        d = {}

    bot_running = subprocess.run(['pgrep','-f','gold_bot.py'], capture_output=True).returncode == 0

    def fmt(v):
        return f"{v:,.2f}" if isinstance(v, (int, float)) else '—'

    return jsonify({
        'price':       fmt(d.get('price')),
        'change':      d.get('change', 0),
        'signal':      d.get('signal', 'HOLD'),
        'time':        d.get('time', ''),
        'rsi':         d.get('rsi', 50),
        'ma20':        fmt(d.get('ma20')),
        'ma50':        fmt(d.get('ma50')),
        'macd':        round(d.get('macd', 0), 2),
        'macd_signal': round(d.get('macd_signal', 0), 2),
        'macd_hist':   round(d.get('macd_hist', 0), 2),
        'bb_upper':    fmt(d.get('bb_upper')),
        'bb_lower':    fmt(d.get('bb_lower')),
        'bb_pos':      d.get('bb_pos', 0.5),
        'bot_running': bot_running,
    })


@app.route('/api/chart_data')
def chart_data():
    try:
        gold = yf.download('GC=F', period='3mo', progress=False, timeout=30)
        if isinstance(gold.columns, pd.MultiIndex):
            gold.columns = gold.columns.get_level_values(0)

        close  = gold['Close']
        ma20   = close.rolling(20).mean()
        ma50   = close.rolling(50).mean()
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()

        dates  = [str(d.date()) for d in gold.index]
        prices = [round(float(v), 2) for v in close]

        def clean(series):
            return [round(float(v), 2) if str(v) != 'nan' else None for v in series]

        signals = []
        try:
            with open(HISTORY_FILE) as f:
                lines = f.readlines()
            prev_sig = None
            for line in lines:
                try:
                    rec = json.loads(line.strip())
                    if rec.get('signal') != prev_sig:
                        signals.append({'time': rec['time'][:10], 'price': rec['price'], 'signal': rec['signal']})
                        prev_sig = rec['signal']
                except Exception:
                    pass
        except Exception:
            pass

        return jsonify({
            'dates':    dates,
            'prices':   prices,
            'ma20':     clean(ma20),
            'ma50':     clean(ma50),
            'bb_upper': clean(bb_mid + 2 * bb_std),
            'bb_lower': clean(bb_mid - 2 * bb_std),
            'signals':  signals,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/signal_history')
def signal_history():
    rows = []
    try:
        with open(HISTORY_FILE) as f:
            lines = f.readlines()

        current_price = None
        try:
            with open(SIGNAL_FILE) as f:
                current_price = json.load(f).get('price')
        except Exception:
            pass

        prev_sig = None
        changes = []
        for line in lines:
            try:
                rec = json.loads(line.strip())
                if rec.get('signal') != prev_sig:
                    changes.append(rec)
                    prev_sig = rec['signal']
            except Exception:
                pass

        for rec in reversed(changes[-20:]):
            since = None
            if current_price and rec.get('price'):
                since = round((current_price - rec['price']) / rec['price'] * 100, 2)
            rows.append({
                'time':   rec.get('time', '')[:16],
                'price':  rec.get('price'),
                'signal': rec.get('signal', ''),
                'since':  since,
            })
    except Exception:
        pass
    return jsonify(rows)


@app.route('/api/logs')
def logs():
    try:
        with open(LOG_FILE) as f:
            lines = f.readlines()
        return ''.join(lines[-60:])
    except Exception:
        return 'No logs yet.'


@app.route('/api/markets_overview')
def markets_overview():
    assets = [
        ('🥇 Gold',        'GC=F'),
        ('🥈 Silver',       'SI=F'),
        ('🇺🇸 S&P 500',    '^GSPC'),
        ('📈 NASDAQ',       '^IXIC'),
        ('🇦🇺 ASX 200',    '^AXJO'),
        ('🇯🇵 Nikkei 225', '^N225'),
        ('🇬🇧 FTSE 100',   '^FTSE'),
        ('🇩🇪 DAX 40',     '^GDAXI'),
        ('🇭🇰 Hang Seng',  '^HSI'),
        ('🇮🇳 SENSEX',     '^BSESN'),
        ('📊 VIX',          '^VIX'),
        ('💵 USD Index',    'DX-Y.NYB'),
    ]
    results = []
    for name, sym in assets:
        try:
            df = yf.download(sym, period='2d', progress=False, timeout=15)
            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)
            if df.empty or len(df) < 2:
                continue
            c  = float(df['Close'].iloc[-1])
            p  = float(df['Close'].iloc[-2])
            ch = round((c - p) / p * 100, 2)
            results.append({'market': name, 'price': f"${c:,.2f}", 'change': ch})
        except Exception:
            pass
    return jsonify(results)


if __name__ == '__main__':
    import os
    os.system('fuser -k 8050/tcp 2>/dev/null')
    app.run(host='0.0.0.0', port=8050, debug=False)
