"""
Telegram Team - Bot management, message handling, channel operations
"""
from typing import List, Dict, Any
from .base import BaseAgent, BaseTeam, AgentConfig, AgentRole


class TelegramBotManagerAgent(BaseAgent):
    """Agent for managing Telegram bots"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class TelegramMessageHandlerAgent(BaseAgent):
    """Agent for handling incoming/outgoing messages"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class TelegramChannelManagerAgent(BaseAgent):
    """Agent for managing channels and groups"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class TelegramTeam(BaseTeam):
    """Telegram Team - Handles bot operations, messaging, and channel management"""
    
    def __init__(self):
        super().__init__("Telegram Team")
    
    def create_agents(self) -> List[BaseAgent]:
        return [
            TelegramBotManagerAgent(AgentConfig(
                name="Telegram Bot Manager",
                role=AgentRole.MANAGER,
                goal="Configure, deploy, and monitor Telegram bots for automated operations",
                backstory="Telegram API expert who builds and maintains production-grade bots. Handles webhook setup, command registration, and rate limiting.",
                tools=["telegram_api", "bot_father", "webhook_manager"],
                llm_config={"model": "gpt-4o", "temperature": 0.3}
            )),
            TelegramMessageHandlerAgent(AgentConfig(
                name="Message Handler",
                role=AgentRole.EXECUTOR,
                goal="Process incoming messages, route to appropriate handlers, send responses",
                backstory="Message processing specialist who handles high-volume chat interactions. Manages conversation state, media handling, and multi-language support.",
                tools=["message_parse", "intent_classify", "response_generate", "media_handle"],
                llm_config={"model": "gpt-4o-mini", "temperature": 0.5}
            )),
            TelegramChannelManagerAgent(AgentConfig(
                name="Channel Manager",
                role=AgentRole.ANALYST,
                goal="Grow and manage Telegram channels/groups, analyze engagement metrics",
                backstory="Community growth expert specializing in Telegram channel optimization. Tracks subscriber growth, engagement rates, and content performance.",
                tools=["channel_stats", "member_management", "content_schedule", "analytics"],
                llm_config={"model": "gpt-4o", "temperature": 0.4}
            )),
        ]
    
    def get_team_config(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "description": "Telegram bot operations, messaging, and community management",
            "agents": [agent.get_config().__dict__ for agent in self.get_agents()],
            "process": "hierarchical",
            "manager": "Telegram Bot Manager",
        }