import json
import platform
import signal
import threading
from queue import Queue, Empty
from time import sleep

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

from fastapi import FastAPI
from fastapi.responses import StreamingResponse
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
    """执行纳斯达克分析任务 (流式响应)"""
    output_queue = Queue()

    def step_callback(step_output):
        try:
            # step_output 可能是 TaskOutput 对象或字典
            msg = ""
            if hasattr(step_output, "thought") and step_output.thought:
                msg = f"🤔 {step_output.thought}"
            elif hasattr(step_output, "output") and step_output.output:
                msg = (
                    f"🔧 Output: {str(step_output.output)[:100]}..."  # 截断一下避免过长
                )
            else:
                msg = str(step_output)

            output_queue.put({"type": "log", "content": msg})
        except Exception as e:
            output_queue.put({"type": "log", "content": f"Step log error: {str(e)}"})

    def run_crew():
        import traceback

        try:
            output_queue.put({"type": "log", "content": "🚀 任务启动..."})

            crew_instance = NasdaqSummaryCrew().crew(step_callback=step_callback)
            result = crew_instance.kickoff()

            # 使用 result.raw 如果存在
            final_content = result.raw if hasattr(result, "raw") else str(result)
            output_queue.put({"type": "result", "content": final_content})

        except Exception as e:
            err_msg = f"执行出错: {str(e)}\n{traceback.format_exc()}"
            output_queue.put({"type": "error", "content": err_msg})
        finally:
            output_queue.put(None)

    # 在后台线程中运行 Crew
    thread = threading.Thread(target=run_crew)
    thread.start()

    def event_generator():
        while True:
            try:
                # 设置超时防止死循环，也可以让 yield 有机会处理断开连接
                data = output_queue.get(timeout=1)

                if data is None:
                    break

                # SSE 格式: data: <json_string>\n\n
                yield f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

            except Empty:
                continue

    return StreamingResponse(event_generator(), media_type="text/event-stream")


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 FastAPI 服务器...")
    print("📡 访问地址: http://localhost:8000")
    print("📋 API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
