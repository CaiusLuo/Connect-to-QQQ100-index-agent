from src.crew import NasdaqSummaryCrew
import os
import requests

TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"


def run_agent_and_notify(chat_id: int, status_msg_id: int):
    """运行 crew_ai 任务并通知用户"""
    import traceback
    
    try:
        # 发送开始消息
        from src.utils.notifier import update_tg_progress
        update_tg_progress(chat_id, status_msg_id, "🚀 任务开始执行...\n正在初始化 AI Agent...")
        
        # 1. 后台执行crew_ai任务
        # 传入 chat_id 和 status_msg_id 以便 Agent 更新进度
        crew_instance = NasdaqSummaryCrew(chat_id, status_msg_id)
        crew = crew_instance.crew()
        
        print(f"✅ Crew 已创建，开始执行任务...")
        result = crew.kickoff()
        print(f"✅ 任务执行完成！")

        # 2. 获取最终结果
        final_content = result.raw if hasattr(result, "raw") else str(result)
        
        # 3. 结果返回用户
        send_url = f"{TG_API_URL}/sendMessage"
        payload_info = {
            "chat_id": chat_id,
            "text": f"✅ 总结生成完毕：\n\n{final_content}",
            "parse_mode": "Markdown",
        }
        response = requests.post(send_url, json=payload_info)
        
        if response.status_code != 200:
            print(f"❌ 发送结果失败: {response.text}")
        else:
            print(f"✅ 结果已发送到 chat_id: {chat_id}")
            
    except Exception as e:
        # 如果出错，也要通知用户
        error_msg = f"❌ 执行出错：{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        
        send_url = f"{TG_API_URL}/sendMessage"
        payload_info = {
            "chat_id": chat_id,
            "text": f"❌ 抱歉，分析过程中出现错误：\n\n{str(e)}",
        }
        requests.post(send_url, json=payload_info)


def update_tg_progress(chat_id, message_id, text):
    """更新 Telegram 消息内容"""
    try:
        send_url = f"{TG_API_URL}/editMessageText"
        payload_info = {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": f"⏳ 实时进度：\n\n{text}",
        }
        
        response = requests.post(send_url, json=payload_info, timeout=5)
        
        if response.status_code == 200:
            print(f"✅ 进度已更新: {text[:50]}...")
        elif response.status_code == 400:
            # 消息内容相同时 Telegram 会返回 400，这是正常的
            resp_json = response.json()
            if "message is not modified" in resp_json.get("description", "").lower():
                print(f"ℹ️ 消息内容未变化，跳过更新")
            else:
                print(f"⚠️ 更新进度失败 (400): {response.text}")
        elif response.status_code == 429:
            # 触发限流
            print(f"⚠️ Telegram API 限流，请降低更新频率")
        else:
            print(f"⚠️ 更新进度失败 ({response.status_code}): {response.text}")
            
    except requests.exceptions.Timeout:
        print(f"⚠️ 更新进度超时")
    except Exception as e:
        print(f"❌ 更新进度出错: {str(e)}")
