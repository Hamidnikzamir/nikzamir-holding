from crewai import Agent, Task, Crew
from crewai.tools import tool
import subprocess
import json

# Tools for the agents
@tool("execute_bash")
def execute_bash(command: str) -> str:
    """Execute a bash command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=60)
        return f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}\nreturncode: {result.returncode}"
    except subprocess.TimeoutExpired:
        return "Command timed out after 60 seconds"
    except Exception as e:
        return f"Error: {str(e)}"

@tool("read_file")
def read_file(path: str) -> str:
    """Read a file and return its content."""
    try:
        with open(path, 'r') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool("write_file")
def write_file(path: str, content: str) -> str:
    """Write content to a file."""
    try:
        with open(path, 'w') as f:
            f.write(content)
        return f"Successfully wrote to {path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

# Manager Agent - analyzes requests and plans tasks
manager = Agent(
    role='Project Manager',
    goal='Analyze incoming requests, break them down into actionable tasks, and coordinate the team',
    backstory='You are an experienced technical project manager who excels at breaking down complex requests into clear, actionable tasks for developers and QA engineers.',
    tools=[read_file, write_file],
    verbose=True,
    allow_delegation=True
)

# Coder Agent - writes code (Python, Bash, etc.)
coder = Agent(
    role='Senior Software Engineer',
    goal='Write clean, efficient, and correct code to implement the required functionality',
    backstory='You are a senior software engineer with expertise in Python, Bash, and automation. You write production-ready code that follows best practices.',
    tools=[execute_bash, read_file, write_file],
    verbose=True,
    allow_delegation=False
)

# QA Agent - tests and validates code
qa = Agent(
    role='QA Engineer',
    goal='Test code thoroughly, find bugs, and ensure quality standards are met',
    backstory='You are a meticulous QA engineer who creates comprehensive test plans, runs tests, and validates that code works correctly in various scenarios.',
    tools=[execute_bash, read_file],
    verbose=True,
    allow_delegation=False
)

def create_crew():
    """Create and return the CrewAI crew."""
    return Crew(
        agents=[manager, coder, qa],
        tasks=[],  # Tasks will be added dynamically
        verbose=True
    )

if __name__ == "__main__":
    crew = create_crew()
    print("CrewAI agents created successfully!")
    print(f"Agents: {[a.role for a in crew.agents]}")