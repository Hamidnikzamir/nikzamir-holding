#!/bin/bash
# Quantum Admin - Startup Script

set -e

echo "🚀 Starting Quantum Admin System..."

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if a port is in use
check_port() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1; then
        return 0
    else
        return 1
    fi
}

# Function to wait for service
wait_for_service() {
    local url=$1
    local name=$2
    local max_attempts=30
    local attempt=1
    
    echo -n "Waiting for $name..."
    while [ $attempt -le $max_attempts ]; do
        if curl -s -f "$url" >/dev/null 2>&1; then
            echo -e " ${GREEN}Ready!${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    echo -e " ${RED}Timeout!${NC}"
    return 1
}

# Check Python environment
echo "🐍 Checking Python environment..."
python --version
pip --version

# Install dependencies if needed
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python -m venv venv
fi

echo "📦 Activating virtual environment..."
source venv/bin/activate

echo "📦 Installing/updating dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for freqtrade config
if [ ! -f "config/freqtrade_config.json" ]; then
    echo -e "${RED}Error: config/freqtrade_config.json not found!${NC}"
    exit 1
fi

# Check if n8n is running
echo "🔍 Checking n8n..."
if check_port 5678; then
    echo -e "${GREEN}✓ n8n is running on port 5678${NC}"
else
    echo -e "${YELLOW}⚠ n8n not detected on port 5678${NC}"
    echo "   Start n8n manually: n8n start"
fi

# Start Freqtrade in background
echo "🤖 Starting Freqtrade..."
if check_port 8080; then
    echo -e "${YELLOW}⚠ Port 8080 already in use (Freqtrade may be running)${NC}"
else
    cd /home/user
    nohup freqtrade trade \
        --config /home/user/quantum-admin/config/freqtrade_config.json \
        --strategy FractalBias \
        --strategy-path /home/user/quantum-admin/src/strategies \
        > /tmp/freqtrade.log 2>&1 &
    FREQTRADE_PID=$!
    echo $FREQTRADE_PID > /tmp/freqtrade.pid
    echo -e "${GREEN}✓ Freqtrade started (PID: $FREQTRADE_PID)${NC}"
    
    # Wait for Freqtrade API
    wait_for_service "http://localhost:8080/api/v1/ping" "Freqtrade API"
fi

# Start Streamlit Dashboard
echo "📊 Starting Streamlit Dashboard..."
if check_port 8501; then
    echo -e "${YELLOW}⚠ Port 8501 already in use (Dashboard may be running)${NC}"
else
    nohup streamlit run src/dashboard/app.py \
        --server.port 8501 \
        --server.address 0.0.0.0 \
        --server.headless true \
        > /tmp/streamlit.log 2>&1 &
    STREAMLIT_PID=$!
    echo $STREAMLIT_PID > /tmp/streamlit.pid
    echo -e "${GREEN}✓ Streamlit started (PID: $STREAMLIT_PID)${NC}"
    
    # Wait for Streamlit
    wait_for_service "http://localhost:8501/_stcore/health" "Streamlit"
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ Quantum Admin System Started!${NC}"
echo "=========================================="
echo ""
echo "📊 Dashboard:  http://localhost:8501"
echo "🤖 Freqtrade API: http://localhost:8080"
echo "🔄 n8n:        http://localhost:5678"
echo ""
echo "📝 Logs:"
echo "   Freqtrade:  tail -f /tmp/freqtrade.log"
echo "   Streamlit:  tail -f /tmp/streamlit.log"
echo ""
echo "🛑 To stop: ./stop.sh"
echo ""

# Keep script running to show logs
echo "Showing Freqtrade logs (Ctrl+C to exit)..."
tail -f /tmp/freqtrade.log