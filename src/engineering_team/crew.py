import os

from crewai import Agent, Crew, Process, Task
from crewai.agents.agent_builder.base_agent import BaseAgent
from crewai.mcp import MCPServerHTTP
from crewai.project import CrewBase, agent, crew, task

from .tools.sandbox_tools import sandbox_tools

LEAD_MODEL = os.getenv("LEAD_MODEL", "openai/gpt-4o")
ENGINEER_MODEL = os.getenv("ENGINEER_MODEL", "openai/gpt-4o-mini")

# Up-to-date library docs, so the team isn't designing against a stale Gradio API.
# The structured config matters: a bare URL string goes through a CrewAI code path
# that sends back sanitized tool names, which breaks Context7's hyphenated tools.
CONTEXT7 = MCPServerHTTP(url="https://mcp.context7.com/mcp")


@CrewBase
class EngineeringTeam:
    """Four agents that design, build, and test a small application."""

    agents: list[BaseAgent]
    tasks: list[Task]

    @agent
    def engineering_lead(self) -> Agent:
        # No sandbox tools: the lead designs, and a lead who can write files
        # starts writing the implementation instead of specifying it. Context7 is
        # read-only docs lookup, so it informs the design without tempting that.
        return Agent(
            config=self.agents_config["engineering_lead"],
            llm=LEAD_MODEL,
            mcps=[CONTEXT7],
        )

    @agent
    def backend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["backend_engineer"],
            tools=sandbox_tools,
            llm=ENGINEER_MODEL,
            max_iter=20,
        )

    @agent
    def frontend_engineer(self) -> Agent:
        return Agent(
            config=self.agents_config["frontend_engineer"],
            tools=sandbox_tools,
            mcps=[CONTEXT7],
            llm=ENGINEER_MODEL,
            max_iter=20,
        )

    @agent
    def test_engineer(self) -> Agent:
        # Highest iteration budget: this agent runs tests, reads failures and
        # fixes code in a loop, which is the whole point of it existing.
        return Agent(
            config=self.agents_config["test_engineer"],
            tools=sandbox_tools,
            llm=ENGINEER_MODEL,
            max_iter=30,
        )

    @task
    def design_task(self) -> Task:
        return Task(config=self.tasks_config["design_task"])

    @task
    def backend_task(self) -> Task:
        return Task(config=self.tasks_config["backend_task"])

    @task
    def frontend_task(self) -> Task:
        return Task(config=self.tasks_config["frontend_task"])

    @task
    def test_task(self) -> Task:
        return Task(config=self.tasks_config["test_task"])

    @crew
    def crew(self) -> Crew:
        # Sequential, not hierarchical: the order here is a real dependency chain
        # (you cannot test code that isn't written), so there is nothing for a
        # manager to decide.
        return Crew(
            agents=self.agents,
            tasks=self.tasks,
            process=Process.sequential,
            verbose=True,
        )
