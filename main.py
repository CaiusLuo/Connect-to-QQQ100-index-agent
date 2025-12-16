from dotenv import load_dotenv

load_dotenv()

from crewai import Crew, Process, Task

from src.crew import NasdaqSummaryCrew

# 实例化自定义的 Crew 类
nasdaq_crew_instance = NasdaqSummaryCrew()
market_analyst_agent = nasdaq_crew_instance.market_analyst()

# 定义任务 (临时在main里定义，通常应在crew.py里定义task方法)
get_data_task = Task(
    config=nasdaq_crew_instance.task_config["fetch_and_analyze_data"],
    agent=market_analyst_agent,
)

# 组装 Crew
nasdaq_crew = Crew(
    agents=[market_analyst_agent],
    tasks=[get_data_task],
    process=Process.sequential,
    verbose=True,
)

# 执行
result = nasdaq_crew.kickoff()
print(result)
