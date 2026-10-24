"""
Media Team - Content generation, image/video processing, multimedia
"""
from typing import List, Dict, Any
from .base import BaseAgent, BaseTeam, AgentConfig, AgentRole


class MediaGeneratorAgent(BaseAgent):
    """Agent for generating media content"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class MediaEditorAgent(BaseAgent):
    """Agent for editing and processing media"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class MediaPublisherAgent(BaseAgent):
    """Agent for publishing media to platforms"""
    
    def create_agent(self):
        return {
            "name": self.config.name,
            "role": self.config.role.value,
            "goal": self.config.goal,
            "backstory": self.config.backstory,
            "tools": self.config.tools,
        }


class MediaTeam(BaseTeam):
    """Media Team - Handles content generation, editing, and multi-platform publishing"""
    
    def __init__(self):
        super().__init__("Media Team")
    
    def create_agents(self) -> List[BaseAgent]:
        return [
            MediaGeneratorAgent(AgentConfig(
                name="Media Generator",
                role=AgentRole.WRITER,
                goal="Generate high-quality images, videos, and audio content using AI tools",
                backstory="Creative technologist specializing in generative AI for multimedia. Masters Midjourney, DALL-E, Runway, ElevenLabs, and Suno for production-grade assets.",
                tools=["image_gen", "video_gen", "audio_gen", "prompt_engineer", "style_transfer"],
                llm_config={"model": "gpt-4o", "temperature": 0.8}
            )),
            MediaEditorAgent(AgentConfig(
                name="Media Editor",
                role=AgentRole.EXECUTOR,
                goal="Edit, enhance, and optimize media assets for each platform's specifications",
                backstory="Post-production expert who optimizes media for web, social, and print. Handles compression, format conversion, branding, and accessibility compliance.",
                tools=["video_edit", "image_edit", "audio_edit", "compress", "watermark", "subtitle"],
                llm_config={"model": "gpt-4o-mini", "temperature": 0.3}
            )),
            MediaPublisherAgent(AgentConfig(
                name="Media Publisher",
                role=AgentRole.MANAGER,
                goal="Distribute media assets across all channels with proper scheduling and metadata",
                backstory="Distribution specialist who manages multi-platform publishing workflows. Ensures consistent branding, optimal timing, and performance tracking.",
                tools=["multi_platform_post", "schedule", "metadata_manage", "analytics_track", "cdn_deploy"],
                llm_config={"model": "gpt-4o", "temperature": 0.3}
            )),
        ]
    
    def get_team_config(self) -> Dict[str, Any]:
        return {
            "team_name": self.team_name,
            "description": "AI-powered media generation, editing, and multi-platform publishing",
            "agents": [agent.get_config().__dict__ for agent in self.get_agents()],
            "process": "sequential",
            "manager": "Media Publisher",
        }