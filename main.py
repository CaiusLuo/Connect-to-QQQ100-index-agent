import platform
import signal

# Windows 平台兼容性修复：这些是 Unix 专用信号，Windows 上不存在
if platform.system() == "Windows":
    # 为 crewai 需要的 Unix 信号定义占位符
    signal.SIGHUP = signal.SIGTERM  # Hangup
    signal.SIGTSTP = signal.SIGTERM  # Terminal Stop
    signal.SIGQUIT = signal.SIGTERM  # Quit
    signal.SIGUSR1 = signal.SIGTERM  # User defined signal 1
    signal.SIGUSR2 = signal.SIGTERM  # User defined signal 2
    signal.SIGCONT = signal.SIGTERM  # Continue
    signal.SIGCHLD = signal.SIGTERM  # Child process status changed
    signal.SIGPIPE = signal.SIGTERM  # Broken pipe
    signal.SIGALRM = signal.SIGTERM  # Alarm clock
    signal.SIGTTIN = signal.SIGTERM  # Background read from tty
    signal.SIGTTOU = signal.SIGTERM  # Background write to tty

from dotenv import load_dotenv

load_dotenv()

from crewai import Crew, Process, Task
from fastapi import FastAPI

from src.crew import NasdaqSummaryCrew

app = FastAPI(
    title="纳斯达克100指数分析 API",
    description="使用 CrewAI 分析纳斯达克100指数(QQQ)的盘后数据",
    version="1.0.0",
)


@app.get("/")
def root():
    """欢迎页面"""
    return {
        "message": "🎯 纳斯达克100指数分析 API",
        "docs": "访问 /docs 查看 API 文档",
        "invoke": "POST /invoke 执行分析任务",
    }


@app.get("/health")
def health():
    """健康检查端点"""
    return {"status": "healthy"}


@app.post("/invoke")
def invoke():
    """执行纳斯达克分析任务"""
    result = nasdaq_crew.kickoff()
    print("============result===========\n", result)
    return {"status": "success", "result": str(result)}


# 实例化自定义的 Crew 类
nasdaq_crew_instance = NasdaqSummaryCrew()
market_analyst_agent = nasdaq_crew_instance.market_analyst()

# 定义任务 (临时在main里定义，通常应在crew.py里定义task方法)
task_config = nasdaq_crew_instance.task_config["fetch_and_analyze_data"]
get_data_task = Task(
    description=task_config["description"],
    expected_output=task_config["expected_output"],
    agent=market_analyst_agent,
)

# 组装 Crew
nasdaq_crew = Crew(
    agents=[market_analyst_agent],
    tasks=[get_data_task],
    process=Process.sequential,
    verbose=True,
)

if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 FastAPI 服务器...")
    print("📡 访问地址: http://localhost:8000")
    print("📋 API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
