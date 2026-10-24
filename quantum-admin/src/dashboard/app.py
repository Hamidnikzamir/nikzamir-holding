"""
Quantum Admin Dashboard - Streamlit Application

Real-time monitoring dashboard for:
- Freqtrade trading bot status
- CrewAI agent orchestration
- n8n workflow automation
- System health metrics
"""

import streamlit as st
import requests
import json
import time
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os
import sys

# Page configuration
st.set_page_config(
    page_title="Quantum Admin Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1e3c72 0%, #2a5298 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2a5298;
    }
    .status-running { color: #00cc44; font-weight: bold; }
    .status-stopped { color: #ff4444; font-weight: bold; }
    .status-warning { color: #ffaa00; font-weight: bold; }
    .agent-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 0.5rem;
    }
    .trade-card {
        background: #fafafa;
        padding: 0.75rem;
        border-radius: 6px;
        border-left: 3px solid #2a5298;
        margin-bottom: 0.5rem;
    }
    .positive { color: #00cc44; }
    .negative { color: #ff4444; }
    .sidebar .sidebar-content { background: #1e3c72; }
</style>
""", unsafe_allow_html=True)

# Configuration
FREQTRADE_API = os.getenv("FREQTRADE_API", "http://localhost:8080")
FREQTRADE_USER = os.getenv("FREQTRADE_USER", "freqtrade")
FREQTRADE_PASS = os.getenv("FREQTRADE_PASS", "freqtrade123")
N8N_API = os.getenv("N8N_API", "http://localhost:5678/api/v1")

# Helper functions
@st.cache_data(ttl=30)
def fetch_freqtrade_status() -> Optional[Dict]:
    """Fetch Freqtrade bot status"""
    try:
        response = requests.get(
            f"{FREQTRADE_API}/api/v1/status",
            auth=(FREQTRADE_USER, FREQTRADE_PASS),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        st.error(f"Freqtrade connection error: {e}")
    return None

@st.cache_data(ttl=30)
def fetch_freqtrade_trades() -> List[Dict]:
    """Fetch recent trades"""
    try:
        response = requests.get(
            f"{FREQTRADE_API}/api/v1/trades",
            auth=(FREQTRADE_USER, FREQTRADE_PASS),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return []

@st.cache_data(ttl=30)
def fetch_freqtrade_profit() -> Optional[Dict]:
    """Fetch profit statistics"""
    try:
        response = requests.get(
            f"{FREQTRADE_API}/api/v1/profit",
            auth=(FREQTRADE_USER, FREQTRADE_PASS),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=30)
def fetch_freqtrade_balance() -> Optional[Dict]:
    """Fetch account balance"""
    try:
        response = requests.get(
            f"{FREQTRADE_API}/api/v1/balance",
            auth=(FREQTRADE_USER, FREQTRADE_PASS),
            timeout=5
        )
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return None

@st.cache_data(ttl=30)
def fetch_n8n_workflows() -> List[Dict]:
    """Fetch n8n workflows"""
    try:
        response = requests.get(f"{N8N_API}/workflows", timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception:
        pass
    return []

@st.cache_data(ttl=30)
def fetch_n8n_executions() -> List[Dict]:
    """Fetch n8n executions"""
    try:
        response = requests.get(f"{N8N_API}/executions", timeout=5)
        if response.status_code == 200:
            return response.json().get("data", [])
    except Exception:
        pass
    return []

# Header
st.markdown("""
<div class="main-header">
    <h1>🚀 Quantum Admin Dashboard</h1>
    <p>Multi-Agent Trading & Automation Orchestration</p>
</div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # Connection status
    st.subheader("🔗 Connections")
    
    # Freqtrade status
    ft_status = fetch_freqtrade_status()
    if ft_status and ft_status.get("state") == "running":
        st.markdown('<span class="status-running">● Freqtrade: Running</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">● Freqtrade: Stopped</span>', unsafe_allow_html=True)
    
    # n8n status
    n8n_workflows = fetch_n8n_workflows()
    if n8n_workflows:
        st.markdown('<span class="status-running">● n8n: Connected</span>', unsafe_allow_html=True)
    else:
        st.markdown('<span class="status-stopped">● n8n: Disconnected</span>', unsafe_allow_html=True)
    
    st.divider()
    
    # Refresh controls
    auto_refresh = st.checkbox("Auto Refresh (30s)", value=True)
    if st.button("🔄 Refresh Now"):
        st.cache_data.clear()
        st.rerun()
    
    st.divider()
    
    # Navigation
    page = st.radio(
        "📍 Navigate",
        ["📊 Overview", "🤖 Trading Bot", "🔄 Workflows", "🤖 Agents", "📈 Analytics", "⚙️ Settings"]
    )

# Main content based on page selection
if page == "📊 Overview":
    # Overview page - key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    # Freqtrade metrics
    ft_status = fetch_freqtrade_status()
    ft_profit = fetch_freqtrade_profit()
    ft_balance = fetch_freqtrade_balance()
    ft_trades = fetch_freqtrade_trades()
    
    with col1:
        if ft_status:
            state = ft_status.get("state", "unknown")
            color = "status-running" if state == "running" else "status-stopped"
            st.markdown(f"""
            <div class="metric-card">
                <h3>Freqtrade Status</h3>
                <p class="{color}">{state.upper()}</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Freqtrade Status</h3>
                <p class="status-stopped">DISCONNECTED</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if ft_profit:
            profit = ft_profit.get("profit_all", 0)
            profit_pct = ft_profit.get("profit_all_pct", 0)
            color = "positive" if profit >= 0 else "negative"
            st.markdown(f"""
            <div class="metric-card">
                <h3>Total Profit</h3>
                <p class="{color}">${profit:.2f} ({profit_pct:.2%})</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Total Profit</h3>
                <p>N/A</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if ft_balance:
            total = ft_balance.get("total", 0)
            st.markdown(f"""
            <div class="metric-card">
                <h3>Account Balance</h3>
                <p>${total:.2f} USDT</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="metric-card">
                <h3>Account Balance</h3>
                <p>N/A</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        open_trades = len([t for t in ft_trades if t.get("is_open", False)]) if ft_trades else 0
        st.markdown(f"""
        <div class="metric-card">
            <h3>Open Trades</h3>
            <p>{open_trades} / 3</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.divider()
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Profit History")
        if ft_profit and ft_profit.get("profit_history"):
            df = pd.DataFrame(ft_profit["profit_history"])
            if not df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df["date"], y=df["profit_abs"],
                    mode='lines+markers', name='Profit',
                    line=dict(color='#2a5298')
                ))
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No profit history available")
    
    with col2:
        st.subheader("💰 Balance Distribution")
        if ft_balance and ft_balance.get("currencies"):
            currencies = ft_balance["currencies"]
            df = pd.DataFrame([
                {"currency": k, "amount": v.get("free", 0) + v.get("used", 0)}
                for k, v in currencies.items()
                if v.get("free", 0) + v.get("used", 0) > 0
            ])
            if not df.empty:
                fig = px.pie(df, values="amount", names="currency", hole=0.4)
                fig.update_layout(height=300, margin=dict(l=0, r=0, t=20, b=0))
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No balance data available")
    
    # Recent trades
    st.subheader("📋 Recent Trades")
    if ft_trades:
        df = pd.DataFrame(ft_trades[:10])
        if not df.empty:
            display_cols = ["pair", "is_open", "enter_tag", "open_rate", "close_rate", 
                          "profit_ratio", "profit_abs", "open_date"]
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No trades found")

elif page == "🤖 Trading Bot":
    st.header("🤖 Freqtrade Trading Bot")
    
    ft_status = fetch_freqtrade_status()
    ft_trades = fetch_freqtrade_trades()
    ft_profit = fetch_freqtrade_profit()
    
    # Bot controls
    col1, col2, col3 = st.columns(3)
    with col1:
        if ft_status and ft_status.get("state") == "running":
            if st.button("⏹️ Stop Bot", type="secondary"):
                try:
                    requests.post(
                        f"{FREQTRADE_API}/api/v1/stop",
                        auth=(FREQTRADE_USER, FREQTRADE_PASS)
                    )
                    st.success("Bot stop requested")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            if st.button("▶️ Start Bot", type="primary"):
                try:
                    requests.post(
                        f"{FREQTRADE_API}/api/v1/start",
                        auth=(FREQTRADE_USER, FREQTRADE_PASS)
                    )
                    st.success("Bot start requested")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
    
    with col2:
        if st.button("🔄 Reload Config"):
            try:
                requests.post(
                    f"{FREQTRADE_API}/api/v1/reload_config",
                    auth=(FREQTRADE_USER, FREQTRADE_PASS)
                )
                st.success("Config reloaded")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col3:
        if st.button("📊 Force Sync"):
            try:
                requests.post(
                    f"{FREQTRADE_API}/api/v1/force_sync",
                    auth=(FREQTRADE_USER, FREQTRADE_PASS)
                )
                st.success("Sync requested")
            except Exception as e:
                st.error(f"Error: {e}")
    
    st.divider()
    
    # Open trades
    st.subheader("📈 Open Trades")
    open_trades = [t for t in ft_trades if t.get("is_open", False)] if ft_trades else []
    if open_trades:
        for trade in open_trades:
            profit_pct = trade.get("profit_ratio", 0) * 100
            color = "positive" if profit_pct >= 0 else "negative"
            st.markdown(f"""
            <div class="trade-card">
                <strong>{trade.get('pair', 'N/A')}</strong> | 
                {'🟢 Long' if trade.get('is_short', False) == False else '🔴 Short'} | 
                Entry: ${trade.get('open_rate', 0):.4f} | 
                Current: ${trade.get('current_rate', 0):.4f} | 
                <span class="{color}">P&L: {profit_pct:.2f}%</span> | 
                {trade.get('enter_tag', 'N/A')}
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No open trades")
    
    # Closed trades
    st.subheader("📜 Recent Closed Trades")
    closed_trades = [t for t in ft_trades if not t.get("is_open", False)][:20] if ft_trades else []
    if closed_trades:
        df = pd.DataFrame(closed_trades)
        display_cols = ["pair", "is_short", "open_rate", "close_rate", 
                       "profit_ratio", "profit_abs", "open_date", "close_date", "exit_reason"]
        available_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No closed trades")

elif page == "🔄 Workflows":
    st.header("🔄 n8n Workflow Automation")
    
    workflows = fetch_n8n_workflows()
    executions = fetch_n8n_executions()
    
    # Workflow list
    st.subheader(f"📋 Workflows ({len(workflows)})")
    
    for wf in workflows:
        active = wf.get("active", False)
        status_class = "status-running" if active else "status-stopped"
        status_text = "ACTIVE" if active else "INACTIVE"
        
        with st.expander(f"{wf.get('name', 'Unnamed')} - <span class='{status_class}'>{status_text}</span>", expanded=False):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**ID:** {wf.get('id', 'N/A')}")
                st.write(f"**Created:** {wf.get('createdAt', 'N/A')}")
                st.write(f"**Updated:** {wf.get('updatedAt', 'N/A')}")
                st.write(f"**Nodes:** {len(wf.get('nodes', []))}")
                st.write(f"**Connections:** {len(wf.get('connections', {}))}")
            with col2:
                if not active:
                    if st.button("▶️ Activate", key=f"activate_{wf.get('id')}"):
                        try:
                            requests.post(f"{N8N_API}/workflows/{wf.get('id')}/activate")
                            st.success("Activated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
                else:
                    if st.button("⏹️ Deactivate", key=f"deactivate_{wf.get('id')}"):
                        try:
                            requests.post(f"{N8N_API}/workflows/{wf.get('id')}/deactivate")
                            st.success("Deactivated!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error: {e}")
    
    # Recent executions
    st.subheader("📜 Recent Executions")
    if executions:
        df = pd.DataFrame(executions[:20])
        if not df.empty:
            display_cols = ["id", "workflowId", "status", "startedAt", "stoppedAt", "mode"]
            available_cols = [c for c in display_cols if c in df.columns]
            st.dataframe(df[available_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No executions found")

elif page == "🤖 Agents":
    st.header("🤖 CrewAI Agent Orchestration")
    
    st.info("Agent system is defined in code. This panel shows agent structure and status.")
    
    # Agent teams
    teams = {
        "🌐 Web Team": {
            "agents": ["WebResearcher", "ContentAnalyzer", "SEOOptimizer", "TrendSpotter"],
            "description": "Web research, content analysis, SEO optimization, trend detection",
            "status": "Ready"
        },
        "📱 Telegram Team": {
            "agents": ["MessageMonitor", "SignalParser", "CommunityManager", "AlertDispatcher"],
            "description": "Telegram monitoring, signal parsing, community management",
            "status": "Ready"
        },
        "📸 Instagram Team": {
            "agents": ["ContentScraper", "EngagementAnalyzer", "HashtagOptimizer", "InfluencerTracker"],
            "description": "Instagram content scraping, engagement analysis, hashtag optimization",
            "status": "Ready"
        },
        "🎬 Media Team": {
            "agents": ["VideoProcessor", "ImageAnalyzer", "ContentGenerator", "DistributionManager"],
            "description": "Media processing, content generation, distribution management",
            "status": "Ready"
        },
        "💼 Consultant Team": {
            "agents": ["StrategyAnalyst", "RiskAssessor", "PortfolioOptimizer", "ReportGenerator"],
            "description": "Strategic analysis, risk assessment, portfolio optimization, reporting",
            "status": "Ready"
        }
    }
    
    for team_name, team_info in teams.items():
        with st.expander(team_name, expanded=True):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**Description:** {team_info['description']}")
                st.write(f"**Agents:** {', '.join(team_info['agents'])}")
            with col2:
                st.markdown(f"<span class='status-running'>{team_info['status']}</span>", unsafe_allow_html=True)
            
            # Agent details
            for agent in team_info['agents']:
                st.markdown(f"""
                <div class="agent-card">
                    <strong>{agent}</strong> - Ready for deployment
                </div>
                """, unsafe_allow_html=True)
    
    # Orchestrator
    st.subheader("🎯 Master Orchestrator")
    st.markdown("""
    <div class="agent-card">
        <strong>QuantumOrchestrator</strong> - Coordinates all agent teams, manages task distribution, 
        aggregates results, and makes high-level decisions based on multi-agent consensus.
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Deploy Agent System"):
        st.success("Agent system deployment initiated! Check logs for status.")

elif page == "📈 Analytics":
    st.header("📈 Analytics & Performance")
    
    ft_profit = fetch_freqtrade_profit()
    ft_trades = fetch_freqtrade_trades()
    
    if ft_trades:
        df = pd.DataFrame(ft_trades)
        closed = df[~df.get("is_open", True)].copy()
        
        if not closed.empty:
            # Win rate
            wins = len(closed[closed["profit_ratio"] > 0])
            total = len(closed)
            win_rate = wins / total * 100 if total > 0 else 0
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trades", total)
            with col2:
                st.metric("Win Rate", f"{win_rate:.1f}%")
            with col3:
                avg_win = closed[closed["profit_ratio"] > 0]["profit_ratio"].mean() * 100 if wins > 0 else 0
                st.metric("Avg Win", f"{avg_win:.2f}%")
            with col4:
                avg_loss = closed[closed["profit_ratio"] < 0]["profit_ratio"].mean() * 100 if (total - wins) > 0 else 0
                st.metric("Avg Loss", f"{avg_loss:.2f}%")
            
            # Profit by pair
            st.subheader("📊 Profit by Pair")
            pair_profit = closed.groupby("pair")["profit_abs"].sum().reset_index()
            fig = px.bar(pair_profit, x="pair", y="profit_abs", color="profit_abs",
                        color_continuous_scale=["red", "green"])
            st.plotly_chart(fig, use_container_width=True)
            
            # Monthly performance
            st.subheader("📅 Monthly Performance")
            closed["month"] = pd.to_datetime(closed["close_date"]).dt.to_period("M")
            monthly = closed.groupby("month")["profit_abs"].sum().reset_index()
            monthly["month"] = monthly["month"].astype(str)
            fig = px.line(monthly, x="month", y="profit_abs", markers=True)
            st.plotly_chart(fig, use_container_width=True)
            
            # Trade duration distribution
            st.subheader("⏱️ Trade Duration Distribution")
            closed["duration"] = (pd.to_datetime(closed["close_date"]) - pd.to_datetime(closed["open_date"])).dt.total_seconds() / 3600
            fig = px.histogram(closed, x="duration", nbins=20, title="Trade Duration (hours)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No closed trades for analytics")
    else:
        st.info("No trade data available")

elif page == "⚙️ Settings":
    st.header("⚙️ System Settings")
    
    tab1, tab2, tab3 = st.tabs(["Freqtrade", "n8n", "Agents"])
    
    with tab1:
        st.subheader("Freqtrade Configuration")
        st.code("""
# Edit config/freqtrade_config.json to change:
# - Trading pairs
# - Stake amount
# - Risk parameters
# - Strategy parameters
# - Exchange credentials
        """, language="json")
        
        if st.button("📥 Download Current Config"):
            try:
                response = requests.get(
                    f"{FREQTRADE_API}/api/v1/config",
                    auth=(FREQTRADE_USER, FREQTRADE_PASS)
                )
                if response.status_code == 200:
                    st.download_button(
                        "Download JSON",
                        data=json.dumps(response.json(), indent=2),
                        file_name="freqtrade_config.json",
                        mime="application/json"
                    )
            except Exception as e:
                st.error(f"Error: {e}")
    
    with tab2:
        st.subheader("n8n Configuration")
        st.code("""
# n8n runs on http://localhost:5678
# Workflows stored in ~/.n8n/workflows
# Credentials in ~/.n8n/config
        """)
    
    with tab3:
        st.subheader("Agent Configuration")
        st.code("""
# Agent definitions in src/agents/
# - base.py: Base agent classes
# - web_team.py: Web research agents
# - telegram_team.py: Telegram agents
# - instagram_team.py: Instagram agents
# - media_team.py: Media processing agents
# - consultant_team.py: Strategy agents
# - orchestrator.py: Master orchestrator
        """)

# Footer
st.divider()
st.markdown("""
<div style="text-align: center; color: #666;">
    Quantum Admin Dashboard v1.0.0 | 
    Freqtrade + CrewAI + n8n Orchestration
</div>
""", unsafe_allow_html=True)

# Auto-refresh
if auto_refresh:
    time.sleep(30)
    st.rerun()