import autogen
from autogen import UserProxyAgent, AssistantAgent
import os

# Configuration for code execution
code_execution_config = {
    "work_dir": "ai-orchestrator/workspace",
    "use_docker": False,
    "last_n_messages": 3,
}

# Create workspace directory
os.makedirs("ai-orchestrator/workspace", exist_ok=True)

# UserProxyAgent - executes code without human input
user_proxy = UserProxyAgent(
    name="UserProxy",
    human_input_mode="NEVER",
    max_consecutive_auto_reply=10,
    is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
    code_execution_config=code_execution_config,
    system_message="You are a user proxy that can execute code. Run the code provided by the assistant and return the results."
)

# Assistant Agent - writes code
assistant = AssistantAgent(
    name="CodeAssistant",
    system_message="You are a helpful AI assistant that writes Python and Bash code to solve tasks. "
                   "Write code in markdown code blocks. The user proxy will execute it.",
    llm_config={
        "config_list": [
            {
                "model": "gpt-4",
                "api_key": os.getenv("OPENAI_API_KEY", ""),
            }
        ]
    }
)

# Alternative: Use a local model or no LLM for simple code execution
# For now, we'll use a simple setup without requiring OpenAI API
assistant_no_llm = AssistantAgent(
    name="CodeAssistant",
    system_message="You are a helpful AI assistant that writes Python and Bash code to solve tasks. "
                   "Write code in markdown code blocks.",
    llm_config=False  # Disable LLM for simple execution tasks
)

def run_autogen_task(task: str):
    """Run a task using AutoGen agents."""
    user_proxy.initiate_chat(assistant_no_llm, message=task)

if __name__ == "__main__":
    print("AutoGen agents created successfully!")
    print(f"UserProxy: {user_proxy.name}")
    print(f"Assistant: {assistant_no_llm.name}")
    print(f"Workspace: {code_execution_config['work_dir']}")