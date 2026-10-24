# Quantum Admin

Multi-agent trading and automation orchestration system combining:
- **Freqtrade** - Algorithmic trading bot with Fractal Bias strategy
- **CrewAI** - Multi-agent orchestration (Web, Telegram, Instagram, Media, Consultant teams)
- **n8n** - Workflow automation
- **Streamlit** - Real-time monitoring dashboard

## Quick Start

### Prerequisites
- Python 3.10+
- n8n installed and running on port 5678
- (Optional) Binance API credentials for live trading

### Installation

```bash
cd quantum-admin
chmod +x start.sh stop.sh
./start.sh
```

This will:
1. Create a virtual environment
2. Install dependencies
3. Start Freqtrade with Fractal Bias strategy
4. Start Streamlit dashboard on port 8501

### Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Dashboard | http://localhost:8501 | - |
| Freqtrade API | http://localhost:8080 | freqtrade / freqtrade123 |
| n8n | http://localhost:5678 | (your n8n setup) |

## Architecture

```
quantum-admin/
├── src/
│   ├── agents/           # CrewAI agent definitions
│   │   ├── base.py       # Base agent classes
│   │   ├── web_team.py   # Web research agents
│   │   ├── telegram_team.py
│   │   ├── instagram_team.py
│   │   ├── media_team.py
│   │   ├── consultant_team.py
│   │   └── orchestrator.py
│   ├── strategies/       # Freqtrade strategies
│   │   └── fractal_bias.py
│   └── dashboard/        # Streamlit dashboard
│       └── app.py
├── config/
│   └── freqtrade_config.json
├── requirements.txt
├── start.sh
├── stop.sh
└── README.md
```

## Fractal Bias Strategy

The Fractal Bias strategy implements Bill Williams' Fractal Theory with multi-timeframe analysis:

- **Higher Timeframe (1h)**: Determines market bias using EMA crossover, RSI, and ADX
- **Current Timeframe (5m)**: Uses Williams Fractals for entry/exit signals
- **Alligator Indicator**: Confirms trend state (awake/trending vs sleeping/ranging)
- **Dynamic Position Sizing**: ATR-based stops with volatility-adjusted leverage

### Key Features
- Multi-timeframe trend alignment
- Fractal-based support/resistance detection
- Volume confirmation
- Dynamic risk management
- Supports both long and short positions

## Agent Teams

### 🌐 Web Team
- **WebResearcher**: Deep web research and data gathering
- **ContentAnalyzer**: Content quality and relevance analysis
- **SEOOptimizer**: Search engine optimization recommendations
- **TrendSpotter**: Emerging trend detection

### 📱 Telegram Team
- **MessageMonitor**: Real-time message monitoring
- **SignalParser**: Trading signal extraction
- **CommunityManager**: Community engagement
- **AlertDispatcher**: Automated alert distribution

### 📸 Instagram Team
- **ContentScraper**: Content harvesting
- **EngagementAnalyzer**: Engagement metrics analysis
- **HashtagOptimizer**: Hashtag strategy optimization
- **InfluencerTracker**: Influencer monitoring

### 🎬 Media Team
- **VideoProcessor**: Video content processing
- **ImageAnalyzer**: Image analysis and tagging
- **ContentGenerator**: Automated content creation
- **DistributionManager**: Multi-platform distribution

### 💼 Consultant Team
- **StrategyAnalyst**: Strategic market analysis
- **RiskAssessor**: Risk evaluation and management
- **PortfolioOptimizer**: Portfolio allocation optimization
- **ReportGenerator**: Automated report generation

### 🎯 Master Orchestrator
- **QuantumOrchestrator**: Coordinates all teams, manages task distribution, aggregates results

## Configuration

### Freqtrade Config
Edit `config/freqtrade_config.json`:
- Trading pairs in `exchange.pair_whitelist`
- Stake amount and risk parameters
- Exchange API credentials (for live trading)
- Strategy parameters

### Environment Variables
```bash
export FREQTRADE_API="http://localhost:8080"
export FREQTRADE_USER="freqtrade"
export FREQTRADE_PASS="freqtrade123"
export N8N_API="http://localhost:5678/api/v1"
```

## Development

### Running Tests
```bash
source venv/bin/activate
pytest tests/ -v
```

### Code Quality
```bash
# Format
black src/

# Lint
ruff check src/

# Type check
mypy src/
```

## Logs

```bash
# Freqtrade
tail -f /tmp/freqtrade.log

# Streamlit
tail -f /tmp/streamlit.log
```

## Stopping

```bash
./stop.sh
```

## Production Deployment

For production:
1. Set `dry_run: false` in freqtrade_config.json
2. Add exchange API credentials
3. Use proper secret management
4. Set up process managers (systemd, PM2, or Docker)
5. Configure reverse proxy with SSL
6. Enable monitoring and alerting

## License

MIT License - See LICENSE file for details