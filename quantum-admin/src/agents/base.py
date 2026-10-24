"""
Base Agent Classes for Quantum Admin
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class AgentRole(Enum):
    """Standard agent roles"""
    RESEARCHER = "researcher"
    ANALYST = "analyst"
    WRITER = "writer"
    REVIEWER = "reviewer"
    MANAGER = "manager"
    EXECUTOR = "executor"


@dataclass
class AgentConfig:
    """Configuration for an agent"""
    name: str
    role: AgentRole
    goal: str
    backstory: str
    tools: List[str] = None
    llm_config: Dict[str, Any] = None
    verbose: bool = True
    allow_delegation: bool = False

    def __post_init__(self):
        if self.tools is None:
            self.tools = []
        if self.llm_config is None:
            self.llm_config = {"model": "gpt-4o-mini", "temperature": 0.7}


class BaseAgent(ABC):
    """Abstract base class for all agents"""
    
    def __init__(self, config: AgentConfig):
        self.config = config
        self._agent = None
    
    @abstractmethod
    def create_agent(self) -> Any:
        """Create the CrewAI agent instance"""
        pass
    
    @property
    def agent(self) -> Any:
        """Lazy-load the agent instance"""
        if self._agent is None:
            self._agent = self.create_agent()
        return self._agent
    
    def get_config(self) -> AgentConfig:
        return self.config


class BaseTeam(ABC):
    """Abstract base class for agent teams"""
    
    def __init__(self, team_name: str):
        self.team_name = team_name
        self.agents: List[BaseAgent] = []
    
    @abstractmethod
    def create_agents(self) -> List[BaseAgent]:
        """Create all agents in the team"""
        pass
    
    def get_agents(self) -> List[BaseAgent]:
        if not self.agents:
            self.agents = self.create_agents()
        return self.agents
    
    def get_agent_by_role(self, role: AgentRole) -> Optional[BaseAgent]:
        for agent in self.get_agents():
            if agent.config.role == role:
                return agent
        return None