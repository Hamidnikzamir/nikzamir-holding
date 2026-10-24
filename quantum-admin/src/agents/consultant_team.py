"""
Consultant Team - Strategy, analysis, reporting, decision support
"""
from typing import List, Dict, Any
from .base import BaseAgent, BaseTeam, AgentConfig, AgentRole


class StrategyConsultantAgent(BaseAgent):
    """Agent for strategic planning and consulting"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class DataAnalystAgent(BaseAgent):
    """Agent for data analysis and insights"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class ReportWriterAgent(BaseAgent):
    """Agent for generating reports and presentations"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class ConsultantTeam(BaseTeam):
    """Consultant Team - Strategic analysis, reporting, and decision support"""
    
    def __init__(self):
        super().__init__("Consultant Team")
    
    def create_agents(self) -> List[BaseAgent]:
        return [
            StrategyConsultantAgent(AgentConfig(
                name="Strategy Consultant",
                role=AgentRole.MANAGER,
                goal="Develop comprehensive strategies based on multi-source intelligence",
                backstory="Senior strategy consultant with experience at top-tier firms. Synthesizes market data, competitive intelligence, and internal metrics into actionable strategic roadmaps.",
                tools=["swot_analysis", "market_sizing", "competitive_map", "scenario_plan", "okr_design"],
                llm_config={"model": "gpt-4o", "temperature": 0.4}
            )),
            DataAnalystAgent(AgentConfig(
                name="Data Analyst",
                role=AgentRole.ANALYST,
                goal="Analyze complex datasets, identify patterns, generate predictive insights",
                backstory="Quantitative analyst expert in statistical modeling, machine learning, and business intelligence. Turns raw data into predictive models and dashboards.",
                tools=["sql_query", "python_analysis", "ml_model", "visualization", "anomaly_detect"],
                llm_config={"model": "gpt-4o", "temperature": 0.2}
            )),
            ReportWriterAgent(AgentConfig(
                name="Report Writer",
                role=AgentRole.WRITER,
                goal="Create executive-ready reports, presentations, and decision briefs",
                backstory="Business communication expert who transforms complex analysis into clear, compelling narratives. Produces board-ready decks, investor memos, and operational dashboards.",
                tools=["report_generate", "slide_create", "executive_summary", "data_storytelling", "template_apply"],
                llm_config={"model": "gpt-4o", "temperature": 0.5}
            )),
        ]
    
    def get_team_config(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "description": "Strategic consulting, data analysis, and executive reporting",
            "agents": [agent.get_config().__dict__ for agent in self.get_agents()],
            "process": "hierarchical",
            "manager": "Strategy Consultant",
        }