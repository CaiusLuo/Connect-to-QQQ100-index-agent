from crewai import Agent, Task, Crew
from src.tools.finance_tool import get_nasdaq_data


class NasdaqSummaryCrew:
    def __init__(self):
        # 自动从 config/ 载入 YAML 配置
        self.agent_config = load_yaml("config/agent.yaml")
        self.task_config = load_yaml("config/task.yaml")

    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agent_config,
            tools=[finance_tool],
        )

    def crew(self) -> Crew:
        return Crew(agent=[self.market_analyst()])
