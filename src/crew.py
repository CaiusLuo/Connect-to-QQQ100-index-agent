import yaml
from crewai import Agent, Crew, Task
from dotenv import load_dotenv

load_dotenv()

from src.tools.finance_tool import get_nasdaq_data
from src.tools.search_tool import search_news_tool


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
            config=self.agent_config["market_analyst"],
            tools=[get_nasdaq_data],
            verbose=True,
        )

    def news_researcher(self) -> Agent:
        return Agent(
            config=self.agent_config["news_researcher"],
            tools=[search_news_tool],
            verbose=True,
        )

    def content_creator(self) -> Agent:
        return Agent(
            config=self.agent_config["content_creator"],
            tools=[],  # 撰写报告不需要额外工具
            verbose=True,
        )

    def fetch_and_analyze_data_task(self) -> Task:
        config = self.task_config["fetch_and_analyze_data"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.market_analyst(),
        )

    def research_key_news_task(self) -> Task:
        config = self.task_config["research_key_news"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.news_researcher(),
        )

    def write_final_report_task(self) -> Task:
        config = self.task_config["write_final_report"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.content_creator(),
            # 依赖上一步的结果
            context=[self.fetch_and_analyze_data_task(), self.research_key_news_task()],
        )

    def crew(self, step_callback=None) -> Crew:
        return Crew(
            agents=[
                self.market_analyst(),
                self.news_researcher(),
                self.content_creator(),
            ],
            tasks=[
                self.fetch_and_analyze_data_task(),
                self.research_key_news_task(),
                self.write_final_report_task(),
            ],
            verbose=True,
            step_callback=step_callback,
        )
