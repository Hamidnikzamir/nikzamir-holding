"""
Quantum Admin - CrewAI Multi-Agent System

Agent Teams:
- Web Team: Web scraping, search, content extraction
- Telegram Team: Telegram bot management, message handling
- Instagram Team: Instagram automation, DM handling
- Media Team: Content generation, image/video processing
- Consultant Team: Strategy, analysis, reporting
"""

from .web_team import WebTeam
from .telegram_team import TelegramTeam
from .instagram_team import InstagramTeam
from .media_team import MediaTeam
from .consultant_team import ConsultantTeam

__all__ = [
    "WebTeam",
    "TelegramTeam",
    "InstagramTeam",
    "MediaTeam",
    "ConsultantTeam",
]