"""
Instagram Team - Automation, DM handling, content posting
"""
from typing import List, Dict, Any
from .base import BaseAgent, BaseTeam, AgentConfig, AgentRole


class InstagramContentAgent(BaseAgent):
    """Agent for Instagram content creation and posting"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class InstagramDMAgent(BaseAgent):
    """Agent for handling Instagram Direct Messages"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        )


class InstagramGrowthAgent(BaseAgent):
    """Agent for Instagram growth strategies"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class InstagramTeam(BaseTeam):
    """Instagram Team - Handles content, DMs, and growth automation"""
    
    def __init__(self):
        super().__init__("Instagram Team")
    
    def create_agents(self) -> List[BaseAgent]:
        return [
            InstagramContentAgent(AgentConfig(
                name="Content Creator",
                role=AgentRole.WRITER,
                goal="Create engaging Instagram posts, stories, and reels with optimal timing",
                backstory="Social media content strategist with expertise in visual storytelling. Creates scroll-stopping content aligned with brand voice and audience interests.",
                tools=["image_generate", "caption_write", "hashtag_research", "post_schedule"],
                llm_config={"model": "gpt-4o", "temperature": 0.7}
            )),
            InstagramDMAgent(AgentConfig(
                name="DM Manager",
                role=AgentRole.EXECUTOR,
                goal="Handle incoming DMs, automate responses, qualify leads",
                backstory="Customer communication specialist who manages high-volume Instagram DMs. Implements auto-replies, lead qualification funnels, and escalation protocols.",
                tools=["dm_read", "dm_send", "lead_qualify", "auto_reply", "template_manage"],
                llm_config={"model": "gpt-4o-mini", "temperature": 0.4}
            )),
            InstagramGrowthAgent(AgentConfig(
                name="Growth Strategist",
                role=AgentRole.ANALYST,
                goal="Analyze account performance, recommend growth strategies, track competitors",
                backstory="Instagram growth hacker who uses data-driven strategies to increase followers, engagement, and conversions. Expert in algorithm optimization.",
                tools=["analytics", "competitor_track", "audience_insights", "growth_plan"],
                llm_config={"model": "gpt-4o", "temperature": 0.3}
            )),
        ]
    
    def get_team_config(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "description": "Instagram content creation, DM automation, and growth strategies",
            "agents": [agent.get_config().__dict__ for agent in self.get_agents()],
            "process": "sequential",
            "manager": "Growth Strategist",
        }