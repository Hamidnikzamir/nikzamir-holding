"""
Quantum Admin Orchestrator - Coordinates all agent teams
"""
from typing import Dict, List, Any, Optional
from .web_team import WebTeam
from .telegram_team import TelegramTeam
from .instagram_team import InstagramTeam
from .media_team import MediaTeam
from .consultant_team import ConsultantTeam
from .base import BaseTeam, AgentRole


class QuantumAdminOrchestrator:
    """Main orchestrator for the Quantum Admin multi-agent system"""
    
    def __init__(self):
        self.teams: Dict[str, BaseTeam] = {
            "web": WebTeam(),
            "telegram": TelegramTeam(),
            "instagram": InstagramTeam(),
            "media": MediaTeam(),
            "consultant": ConsultantTeam(),
        }
        self._initialize_all_agents()
    
    def _initialize_all_agents(self):
        """Pre-initialize all agents in all teams"""
        for team in self.teams.values():
            team.get_agents()
    
    def get_team(self, team_name: str) -> Optional[BaseTeam]:
        """Get a specific team by name"""
        return self.teams.get(team_name.lower())
    
    def get_all_teams(self) -> Dict[str, BaseTeam]:
        """Get all teams"""
        return self.teams
    
    def get_all_agents(self) -> List[Dict[str, Any]]:
        """Get all agents across all teams"""
        all_agents = []
        for team_name, team in self.teams.items():
            for agent in team.get_agents():
                config = agent.get_config()
                all_agents.append({
                    "team": team_name,
                    "name": config.name,
                    "role": config.role.value,
                    "goal": config.goal,
                    "tools": config.tools,
                    "llm_config": config.llm_config,
                })
        return all_agents
    
    def get_agents_by_role(self, role: AgentRole) -> List[Dict[str, Any]]:
        """Get all agents with a specific role across all teams"""
        agents = []
        for team_name, team in self.teams.items():
            agent = team.get_agent_by_role(role)
            if agent:
                config = agent.get_config()
                agents.append({
                    "team": team_name,
                    "name": config.name,
                    "role": config.role.value,
                    "goal": config.goal,
                    "tools": config.tools,
                })
        return agents
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        total_agents = sum(len(team.get_agents()) for team in self.teams.values())
        return {
            "system": "Quantum Admin",
            "version": "1.0.0",
            "teams_count": len(self.teams),
            "total_agents": total_agents,
            "teams": {
                name: {
                    "name": team.team_name,
                    "agent_count": len(team.get_agents()),
                    "agents": [a.get_config().name for a in team.get_agents()],
                }
                for name, team in self.teams.items()
            },
            "status": "operational",
        }
    
    def execute_workflow(self, workflow_name: str, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a predefined workflow across teams
        This is a placeholder for actual CrewAI crew execution
        """
        workflows = {
            "market_research": {
                "description": "Comprehensive market research using Web + Consultant teams",
                "teams": ["web", "consultant"],
                "steps": [
                    {"team": "web", "agent": "Web Researcher", "task": "Research market trends and competitors"},
                    {"team": "web", "agent": "Content Analyst", "task": "Analyze and synthesize findings"},
                    {"team": "consultant", "agent": "Strategy Consultant", "task": "Develop strategic recommendations"},
                    {"team": "consultant", "agent": "Report Writer", "task": "Create executive report"},
                ]
            },
            "social_media_campaign": {
                "description": "End-to-end social media campaign using Instagram + Media + Consultant teams",
                "teams": ["instagram", "media", "consultant"],
                "steps": [
                    {"team": "consultant", "agent": "Strategy Consultant", "task": "Define campaign strategy and KPIs"},
                    {"team": "media", "agent": "Media Generator", "task": "Generate visual assets"},
                    {"team": "media", "agent": "Media Editor", "task": "Optimize assets for Instagram"},
                    {"team": "instagram", "agent": "Content Creator", "task": "Write captions and schedule posts"},
                    {"team": "instagram", "agent": "Growth Strategist", "task": "Plan growth tactics"},
                ]
            },
            "lead_generation": {
                "description": "Automated lead gen using Web + Telegram + Instagram teams",
                "teams": ["web", "telegram", "instagram"],
                "steps": [
                    {"team": "web", "agent": "Web Researcher", "task": "Identify target prospects"},
                    {"team": "web", "agent": "Web Scraper", "task": "Extract contact information"},
                    {"team": "telegram", "agent": "Message Handler", "task": "Send outreach via Telegram"},
                    {"team": "instagram", "agent": "DM Manager", "task": "Send outreach via Instagram DM"},
                ]
            },
        }
        
        if workflow_name not in workflows:
            return {"error": f"Unknown workflow: {workflow_name}", "available": list(workflows.keys())}
        
        workflow = workflows[workflow_name]
        return {
            "workflow": workflow_name,
            "description": workflow["description"],
            "status": "defined",
            "steps": workflow["steps"],
            "inputs": inputs,
            "note": "This is a workflow definition. Actual execution requires CrewAI runtime.",
        }


# Singleton instance
_orchestrator: Optional[QuantumAdminOrchestrator] = None


def get_orchestrator() -> QuantumAdminOrchestrator:
    """Get or create the singleton orchestrator instance"""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = QuantumAdminOrchestrator()
    return _orchestrator