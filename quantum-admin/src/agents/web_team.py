"""
Web Team - Web scraping, search, content extraction
"""
from typing import List, Dict, Any
from .base import BaseAgent, BaseTeam, AgentConfig, AgentRole


class WebResearcherAgent(BaseAgent):
    """Agent for web research and information gathering"""
    
    def create_agent(self):
        # This will be replaced with actual CrewAI agent when dependencies are installed
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class WebScraperAgent(BaseAgent):
    """Agent for web scraping and data extraction"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class ContentAnalyzerAgent(BaseAgent):
    """Agent for analyzing extracted content"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class WebTeam(BaseTeam):
    """Web Team - Handles web research, scraping, and content analysis"""
    
    def __init__(self):
        super().__init__("Web Team")
    
    def create_agents(self) -> List[BaseAgent]:
        return [
            WebResearcherAgent(AgentConfig(
                name="Web Researcher",
                role=AgentRole.RESEARCHER,
                goal="Find accurate, up-to-date information from the web on any topic",
                backstory="Expert web researcher with 10+ years experience in competitive intelligence, market research, and fact-checking. Known for finding needles in haystacks.",
                tools=["web_search", "web_scrape", "api_request"],
                llm_config={"model": "gpt-4o", "temperature": 0.3}
            )),
            WebScraperAgent(AgentConfig(
                name="Web Scraper",
                role=AgentRole.EXECUTOR,
                goal="Extract structured data from websites efficiently and reliably",
                backstory="Technical specialist in web scraping, HTML parsing, and data extraction. Handles dynamic content, pagination, and anti-bot measures.",
                tools=["web_scrape", "html_parse", "json_extract"],
                llm_config={"model": "gpt-4o-mini", "temperature": 0.2}
            )),
            ContentAnalyzerAgent(AgentConfig(
                name="Content Analyst",
                role=AgentRole.ANALYST,
                goal="Analyze and synthesize web content into actionable insights",
                backstory="Content analysis expert who transforms raw web data into structured intelligence. Skilled in sentiment analysis, trend detection, and competitive benchmarking.",
                tools=["text_analysis", "sentiment_analysis", "trend_detection"],
                llm_config={"model": "gpt-4o", "temperature": 0.4}
            )),
        ]
    
    def get_team_config(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "description": "Web research, scraping, and content intelligence",
            "agents": [agent.get_config().__dict__ for agent in self.get_agents()],
            "process": "sequential",
            "manager": "Web Researcher",
        }