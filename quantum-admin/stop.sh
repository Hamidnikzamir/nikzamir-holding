#!/bin/bash
# Quantum Admin - Stop Script

echo "🛑 Stopping Quantum Admin System..."

# Stop Freqtrade
if [ -f /tmp/freqtrade.pid ]; then
    PID=$(cat /tmp/freqtrade.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Freqtrade (PID: $PID)..."
        kill $PID
        sleep 2
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
        fi
        echo "✓ Freqtrade stopped"
    fi
    rm -f /tmp/freqtrade.pid
fi

# Stop Streamlit
if [ -f /tmp/streamlit.pid ]; then
    PID=$(cat /tmp/streamlit.pid)
    if kill -0 $PID 2>/dev/null; then
        echo "Stopping Streamlit (PID: $PID)..."
        kill $PID
        sleep 1
        if kill -0 $PID 2>/dev/null; then
            kill -9 $PID
        fi
        echo "✓ Streamlit stopped"
    fi
    rm -f /tmp/streamlit.pid
fi

# Also kill any remaining processes on ports
for port in 8080 8501; do
    PID=$(lsof -ti :$port)
    if [ ! -z "$PID" ]; then
        echo "Killing process on port $port (PID: $PID)..."
        kill -9 $PID 2>/dev/null
    fi
done

echo "✅ All services stopped"