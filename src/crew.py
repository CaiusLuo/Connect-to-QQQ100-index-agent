import yaml
from crewai import Agent, Crew

from src.tools.finance_tool import get_nasdaq_data


def load_yaml(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


class NasdaqSummaryCrew:
    def __init__(self):
        # 自动从 config/ 载入 YAML 配置
        self.agent_config = load_yaml("config/agent.yaml")
        self.task_config = load_yaml("config/task.yaml")

    def market_analyst(self) -> Agent:
        return Agent(
            config=self.agent_config["market_analyst"],  # 指向具体的配置项
            tools=[get_nasdaq_data],
            verbose=True,
        )

    def crew(self) -> Crew:
        return Crew(agent=[self.market_analyst()])
