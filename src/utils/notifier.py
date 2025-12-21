from src.crew import NasdaqSummaryCrew
import os
import requests

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"


def run_agent_and_notify(chat_id: int, status_msg_id: int):
    """运行 crew_ai 任务并通知用户"""
    # 1. 后台执行crew_ai任务
    # 传入 chat_id 和 status_msg_id 以便 Agent 更新进度
    crew = NasdaqSummaryCrew(chat_id, status_msg_id).crew()
    result = crew.kickoff()

    # 2. 结果返回用户
    send_url = f"{TG_API_URL}/sendMessage"
    payload_info = {
        "chat_id": chat_id,
        "text": f"✅总结生成完毕：\n\n {result.raw}",
        "parse_mode": "Markdown",
    }
    requests.post(send_url, json=payload_info)


def update_tg_progress(chat_id, message_id, text):
    """更新 Telegram 消息内容"""
    send_url = f"{TG_API_URL}/editMessageText"
    payload_info = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": f"⏳ **实时进度：**\n\n{text}",
        "parse_mode": "Markdown",
    }
    requests.post(send_url, json=payload_info)
