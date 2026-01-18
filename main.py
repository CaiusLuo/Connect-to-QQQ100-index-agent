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

from fastapi import FastAPI, Request, BackgroundTasks
from fastapi.responses import StreamingResponse
import requests
from src.crew import NasdaqSummaryCrew
from src.utils.notifier import run_agent_and_notify, TG_API_URL
from src.utils.scheduler import get_scheduler, get_user_stats
from src.db.tg_user.user_service import UserService
from src.utils.auth import check_admin_permission, get_admin_help, is_admin

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
        "webhook": "POST /webhook Telegram Bot 接口",
        "scheduler": "定时推送功能已启用 (09:00, 20:00)",
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


@app.post("/webhook")
async def telegram_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
):
    """TG机器人回复(webhook)"""
    data = await request.json()
    if "message" in data:
        chat_id = data["message"]["chat"]["id"]
        text = data["message"].get("text", "")
        user_data = data["message"]["from"]

        # 记录所有与 Bot 互动的用户（自动订阅）
        try:
            UserService.subscribe_user(user_data)
            print(f"✅ 用户信息已更新: {chat_id}")
        except Exception as e:
            print(f"❌ 更新用户信息失败: {str(e)}")

        print(f"收到消息: {text} (来自用户: {chat_id})")

        if text in ["/start_summary"]:
            initial_msg = {
                "chat_id": chat_id,
                "text": "🚀 收到请求！正在调动 AI 智能体分析纳指数据，请稍候...",
            }
            response = requests.post(TG_API_URL + "/sendMessage", json=initial_msg)
            if response.status_code == 200:
                resp_data = response.json()
                # 拿回发出的消息ID，用于后续更新进度
                status_msg_id = resp_data["result"]["message_id"]
                background_tasks.add_task(run_agent_and_notify, chat_id, status_msg_id)
            else:
                print(f"Failed to send initial message: {response.text}")
        
        elif text in ["/unsubscribe", "/取消订阅"]:
            # 取消订阅定时推送
            try:
                UserService.unsubscribe_user(user_data)
                msg = "❌ 已取消订阅定时推送。如需重新订阅，请发送 /subscribe"
            except Exception as e:
                print(f"❌ 取消订阅失败: {str(e)}")
                msg = "⚠️ 取消订阅失败，请稍后重试。"
            
            requests.post(TG_API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": msg
            })
        
        elif text in ["/subscribe", "/订阅"]:
            # 重新订阅定时推送
            try:
                UserService.subscribe_user(user_data)
                msg = "✅ 订阅成功！您将在每日 09:00 和 20:00 收到纳斯达克100指数分析报告。"
            except Exception as e:
                print(f"❌ 订阅失败: {str(e)}")
                msg = "⚠️ 订阅失败，请稍后重试。"
            
            requests.post(TG_API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": msg
            })
        
        elif text in ["/status", "/状态"]:
            # 查看订阅状态 - 仅管理员可用
            has_permission, error_msg = check_admin_permission(chat_id)
            
            if not has_permission:
                requests.post(TG_API_URL + "/sendMessage", json={
                    "chat_id": chat_id,
                    "text": error_msg
                })
                return {"status": "ok"}
            
            try:
                stats = get_user_stats()
                
                # 管理员详细状态信息
                status_msg = f"""
🛡️ 系统管理面板

📊 用户统计：
• 订阅用户数：{stats['subscribed_count']}
• 活跃用户：{len([u for u in stats['users'] if u])}

⏰ 定时任务：
• 推送时间：每日 09:00 和 20:00
• 状态：运行中 ✅

💾 数据存储：
• 类型：PostgreSQL 数据库
• 状态：连接正常 ✅

🤖 Bot 信息：
• 管理员ID：{chat_id}
• 权限：完全访问 🔓

📋 最近订阅用户：
{chr(10).join([f"• {u[1] or u[2] or 'Unknown'} ({u[0]})" for u in stats['users'][:5]])}
                """
                
                if stats['subscribed_count'] > 5:
                    status_msg += f"\n... 还有 {stats['subscribed_count'] - 5} 个用户"
                    
            except Exception as e:
                print(f"❌ 获取状态失败: {str(e)}")
                status_msg = f"⚠️ 获取系统状态失败：{str(e)}"
            
            requests.post(TG_API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": status_msg.strip()
            })
        
        elif text in ["/admin_help", "/管理员帮助"]:
            # 管理员帮助 - 仅管理员可用
            has_permission, error_msg = check_admin_permission(chat_id)
            
            if not has_permission:
                requests.post(TG_API_URL + "/sendMessage", json={
                    "chat_id": chat_id,
                    "text": error_msg
                })
                return {"status": "ok"}
            
            help_msg = get_admin_help()
            
            requests.post(TG_API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": help_msg.strip()
            })
        
        elif text in ["/help", "/帮助", "/start"]:
            # 帮助信息 - 根据用户权限显示不同内容
            if is_admin(chat_id):
                # 管理员帮助信息
                help_msg = f"""
🤖 纳斯达克100指数分析机器人 (管理员模式)

👋 欢迎管理员！您拥有完全访问权限。

📋 普通命令：
• /start_summary - 立即生成分析报告
• /unsubscribe 或 /取消订阅 - 取消定时推送
• /subscribe 或 /订阅 - 重新订阅定时推送
• /help 或 /帮助 - 显示此帮助信息

🛡️ 管理员专用命令：
• /status 或 /状态 - 查看系统状态和用户统计
• /admin_help - 显示管理员详细帮助

⏰ 定时推送时间：
• 上午 09:00 - 开盘前分析
• 晚上 20:00 - 盘后分析

💡 所有与机器人互动的用户都会自动订阅定时推送
💾 用户数据安全存储在数据库中
🔐 您当前以管理员身份登录
                """
            else:
                # 普通用户帮助信息
                help_msg = f"""
🤖 纳斯达克100指数分析机器人

👋 欢迎！您已自动订阅定时推送。

📋 可用命令：
• /start_summary - 立即生成分析报告
• /unsubscribe 或 /取消订阅 - 取消定时推送
• /subscribe 或 /订阅 - 重新订阅定时推送
• /help 或 /帮助 - 显示此帮助信息

⏰ 定时推送时间：
• 上午 09:00 - 开盘前分析
• 晚上 20:00 - 盘后分析

💡 所有与机器人互动的用户都会自动订阅定时推送
💾 用户数据安全存储在数据库中
                """
            
            requests.post(TG_API_URL + "/sendMessage", json={
                "chat_id": chat_id,
                "text": help_msg.strip()
            })
        
        return {"status": "ok"}
    return {"status": "error"}


# 使用新的生命周期事件
@app.on_event("startup")
async def startup_event():
    """应用启动时执行的操作"""
    print("🚀 启动定时任务调度器...")
    get_scheduler()  # 启动调度器


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行的操作"""
    scheduler = get_scheduler()
    if scheduler:
        scheduler.shutdown()
        print("⏹️ 定时任务调度器已关闭")


if __name__ == "__main__":
    import uvicorn

    print("🚀 启动 FastAPI 服务器...")
    print("📡 访问地址: http://localhost:8000")
    print("📋 API 文档: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000)
