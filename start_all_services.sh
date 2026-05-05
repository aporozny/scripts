#!/bin/bash
echo "🚀 Starting All Services..."
cd /home/andre
source /home/andre/envs/gold-venv/bin/activate

# OpenClaw (already running via system)
echo "🦞 OpenClaw: Already running"

# OpenJarvis API
pkill -f "jarvis serve" 2>/dev/null
nohup jarvis serve --host 0.0.0.0 --port 8080 > /home/andre/logs/jarvis.log 2>&1 &
sleep 2
echo "🤖 OpenJarvis API: Started (Port 8080)"

# Jarvis Frontend
pkill -f jarvis_frontend 2>/dev/null
nohup python /home/andre/scripts/jarvis_frontend.py > /home/andre/logs/jarvis_frontend.log 2>&1 &
sleep 2
echo "💬 Jarvis Chat: Started (Port 5000)"

# Market Dashboard
fuser -k 8050/tcp 2>/dev/null
nohup python /home/andre/scripts/market_dashboard.py > /home/andre/logs/dashboard.log 2>&1 &
sleep 2
echo "📊 Market Dashboard: Started (Port 8050)"

# Gold Bot
pkill -f gold_bot.py 2>/dev/null
nohup python /home/andre/scripts/gold_bot.py > /home/andre/logs/gold_bot.log 2>&1 &
sleep 1
echo "🥇 Gold Bot: Started"

echo ""
echo "========================================="
echo "✅ ALL SERVICES RUNNING!"
echo "========================================="
echo "📊 Dashboard:  http://$(hostname -I | awk '{print $1}'):8050"
echo "💬 Jarvis AI:  http://$(hostname -I | awk '{print $1}'):5000"
echo "🤖 Jarvis API: http://$(hostname -I | awk '{print $1}'):8080"
echo "🦞 OpenClaw:   http://$(hostname -I | awk '{print $1}'):18765"
