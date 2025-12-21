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
        self.task_count = 0  # 任务计数器
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

    def _create_task_callback(self):
        """创建任务回调，在每个任务完成时更新进度"""
        
        def callback(task_output):
            self.task_count += 1
            
            # 只有在有 chat_id 和 status_msg_id 时才更新 Telegram
            if not (self.chat_id and self.status_msg_id):
                return
            
            # 延迟导入避免循环依赖
            from src.utils.notifier import update_tg_progress
            
            print(f"\n✅ [任务 #{self.task_count}] Task callback 触发！")
            
            # 提取任务信息
            task_desc = getattr(task_output, "description", "")
            task_summary = getattr(task_output, "summary", "")
            raw_output = getattr(task_output, "raw", "")
            
            # 构建进度文本
            progress_parts = []
            
            if self.task_count == 1:
                progress_parts.append(f"✅ 任务 1/3 完成：数据获取与分析")
            elif self.task_count == 2:
                progress_parts.append(f"✅ 任务 2/3 完成：新闻研究")
            elif self.task_count == 3:
                progress_parts.append(f"✅ 任务 3/3 完成：报告撰写")
            else:
                progress_parts.append(f"✅ 任务 {self.task_count} 完成")
            
            # 添加任务摘要（截取前200字符）
            if task_summary:
                summary_preview = task_summary[:200] + "..." if len(task_summary) > 200 else task_summary
                progress_parts.append(f"\n📝 摘要: {summary_preview}")
            elif raw_output:
                output_preview = str(raw_output)[:200] + "..." if len(str(raw_output)) > 200 else str(raw_output)
                progress_parts.append(f"\n📝 输出: {output_preview}")
            
            progress_text = "\n".join(progress_parts)
            
            print(f"   📤 更新 Telegram 消息: {progress_text[:100]}...")
            
            # 更新消息
            update_tg_progress(self.chat_id, self.status_msg_id, progress_text)

        return callback

    def _create_step_callback(self):
        """创建闭包,捕获当前请求的ID,用于更新Telegram消息"""
        import time
        self._last_update_time = 0  # 用于限流
        self._callback_count = 0  # 统计回调次数
        
        def callback(step_output):
            self._callback_count += 1
            print(f"\n🔔 [回调 #{self._callback_count}] Step callback 触发！")
            
            # 只有在有 chat_id 和 status_msg_id 时才更新 Telegram
            if not (self.chat_id and self.status_msg_id):
                print(f"   ⚠️ 没有 chat_id 或 status_msg_id，跳过 Telegram 更新")
                return
                
            # 限流：至少间隔1秒才更新一次（避免Telegram API限制）
            current_time = time.time()
            if current_time - self._last_update_time < 1:
                print(f"   ⏱️ 限流中，距离上次更新 {current_time - self._last_update_time:.2f}秒")
                return
            self._last_update_time = current_time
            
            # 延迟导入避免循环依赖
            from src.utils.notifier import update_tg_progress
            
            # 打印调试信息
            step_type = type(step_output).__name__
            print(f"\n📊 Step Callback 触发 - 类型: {step_type}")
            
            if hasattr(step_output, "__dict__"):
                print(f"   属性: {step_output.__dict__}")
            
            # 构建进度文本
            progress_parts = []
            
            # 根据不同类型提取信息
            # ToolResult: 工具执行结果
            if step_type == "ToolResult":
                tool_name = getattr(step_output, "tool", "未知工具")
                result = getattr(step_output, "result", "")
                progress_parts.append(f"🔧 工具: {tool_name}")
                if result:
                    result_preview = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                    progress_parts.append(f"📤 结果: {result_preview}")
            
            # AgentAction: Agent 执行动作
            elif step_type == "AgentAction":
                tool = getattr(step_output, "tool", "")
                tool_input = getattr(step_output, "tool_input", "")
                log = getattr(step_output, "log", "")
                
                if tool:
                    progress_parts.append(f"🔧 调用工具: {tool}")
                
                if tool_input:
                    input_preview = str(tool_input)[:150] + "..." if len(str(tool_input)) > 150 else str(tool_input)
                    progress_parts.append(f"📥 输入: {input_preview}")
                
                if log:
                    log_preview = log[:200] + "..." if len(log) > 200 else log
                    progress_parts.append(f"💭 思考: {log_preview}")
            
            # AgentFinish: Agent 完成任务
            elif step_type == "AgentFinish":
                output = getattr(step_output, "return_values", {})
                log = getattr(step_output, "log", "")
                
                progress_parts.append(f"✅ Agent 完成任务")
                
                if log:
                    log_preview = log[:200] + "..." if len(log) > 200 else log
                    progress_parts.append(f"📝 总结: {log_preview}")
            
            # 其他类型：尝试通用属性
            else:
                # 尝试常见属性
                for attr in ["tool", "action", "thought", "output", "result"]:
                    value = getattr(step_output, attr, None)
                    if value:
                        value_str = str(value)[:150] + "..." if len(str(value)) > 150 else str(value)
                        progress_parts.append(f"{attr}: {value_str}")
            
            if progress_parts:
                progress_text = "\n\n".join(progress_parts)
            else:
                progress_text = f"Agent 正在处理任务... (类型: {step_type})"
            
            print(f"   📤 准备更新 Telegram 消息: {progress_text[:100]}...")
            
            # 更新消息
            update_tg_progress(self.chat_id, self.status_msg_id, progress_text)

        return callback

    def crew(self, step_callback=None, task_callback=None) -> Crew:
        # 如果外部传入了回调，使用外部的；否则使用内部的
        step_cb = step_callback if step_callback else self._create_step_callback()
        task_cb = task_callback if task_callback else self._create_task_callback()
        
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
            step_callback=step_cb,  # Step 级别回调
            task_callback=task_cb,  # Task 级别回调（更可靠）
        )

