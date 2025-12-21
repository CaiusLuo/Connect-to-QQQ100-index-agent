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
    def __init__(self, chat_id, status_msg_id):
        self.chat_id = chat_id
        self.status_msg_id = status_msg_id
        # 自动从 config/ 载入 YAML 配置
        self.agent_config = load_yaml("config/agent.yaml")
        self.task_config = load_yaml("config/task.yaml")

    def market_analyst(self) -> Agent:
        """市场分析师"""
        return Agent(
            config=self.agent_config["market_analyst"],
            tools=[get_nasdaq_data],
            verbose=True,
        )

    def news_researcher(self) -> Agent:
        """新闻研究员"""
        return Agent(
            config=self.agent_config["news_researcher"],
            tools=[search_news_tool],
            verbose=True,
        )

    def content_creator(self) -> Agent:
        """内容创作者"""
        return Agent(
            config=self.agent_config["content_creator"],
            tools=[],  # 撰写报告不需要额外工具
            verbose=True,
        )

    def fetch_and_analyze_data_task(self) -> Task:
        """获取并分析数据"""
        config = self.task_config["fetch_and_analyze_data"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.market_analyst(),
        )

    def research_key_news_task(self) -> Task:
        """研究关键新闻"""
        config = self.task_config["research_key_news"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.news_researcher(),
        )

    def write_final_report_task(self) -> Task:
        """撰写最终报告"""
        config = self.task_config["write_final_report"]
        return Task(
            description=config["description"],
            expected_output=config["expected_output"],
            agent=self.content_creator(),
            # 依赖上一步的结果
            context=[self.fetch_and_analyze_data_task(), self.research_key_news_task()],
        )

    def _create_step_callback(self):
        """创建闭包,捕获当前请求的ID,用于更新Telegram消息"""

        def callback(step):
            thought = getattr(step, "thought", "思考中...")
            tool = getattr(step, "tool", "调用工具中...")

            progress_text = f"Agent 正在执行: {tool}\n 内容摘要: {thought[:100]}..."

            # 更新消息
            update_tg_progress(self.chat_id, self.status_msg_id, progress_text)

        return callback

    def crew(self) -> Crew:
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
            step_callback=self._create_step_callback(),  # 绑定动态回调
        )
