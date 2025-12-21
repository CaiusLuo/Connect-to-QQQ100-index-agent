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
    def __init__(self, chat_id=None, status_msg_id=None):
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
            # 只有在有 chat_id 和 status_msg_id 时才更新 Telegram
            if self.chat_id and self.status_msg_id:
                # 延迟导入避免循环依赖
                from src.utils.notifier import update_tg_progress
                
                thought = getattr(step, "thought", "思考中...")
                tool = getattr(step, "tool", "调用工具中...")

                progress_text = f"Agent 正在执行: {tool}\n 内容摘要: {thought[:100]}..."

                # 更新消息
                update_tg_progress(self.chat_id, self.status_msg_id, progress_text)

        return callback

    def crew(self, step_callback=None) -> Crew:
        # 如果外部传入了 step_callback，使用外部的；否则使用内部的
        callback = step_callback if step_callback else self._create_step_callback()
        
        # 创建任务实例（必须使用同一个实例来建立依赖关系）
        task1 = self.fetch_and_analyze_data_task()
        task2 = self.research_key_news_task()
        task3 = Task(
            description=self.task_config["write_final_report"]["description"],
            expected_output=self.task_config["write_final_report"]["expected_output"],
            agent=self.content_creator(),
            context=[task1, task2],  # 使用同一个实例引用
        )
        
        return Crew(
            agents=[
                self.market_analyst(),
                self.news_researcher(),
                self.content_creator(),
            ],
            tasks=[task1, task2, task3],
            verbose=True,
            step_callback=callback,  # 使用选定的回调
        )
