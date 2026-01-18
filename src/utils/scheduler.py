# 定时任务处理
import os
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from src.utils.notifier import run_agent_and_notify
from src.db.tg_user.user_service import UserService
import requests

# 从环境变量获取配置
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"

executors = {
    'default': ThreadPoolExecutor(10)
}

def send_scheduled_report():
    """发送定时报告给所有订阅用户"""
    try:
        # 从数据库获取所有订阅用户
        subscribed_users = UserService.list_subscribed_users()
        
        if not subscribed_users:
            print("⚠️ 没有订阅用户，跳过定时推送")
            return
        
        print(f"📅 开始定时推送，目标用户数: {len(subscribed_users)}")
        
        for user in subscribed_users:
            # user 是一个元组: (tg_user_id, username, first_name, last_name)
            chat_id = user[0]  # tg_user_id
            username = user[1] or user[2] or "用户"  # username 或 first_name
            
            try:
                # 发送初始消息
                initial_msg = {
                    "chat_id": chat_id,
                    "text": f"� 定时推新送：正在生成纳斯达克100指数分析报告...\n\n💡 如不需要定时推送，请发送 /unsubscribe",
                }
                response = requests.post(TG_API_URL + "/sendMessage", json=initial_msg)
                
                if response.status_code == 200:
                    resp_data = response.json()
                    status_msg_id = resp_data["result"]["message_id"]
                    
                    # 异步执行分析任务
                    run_agent_and_notify(chat_id, status_msg_id)
                    print(f"✅ 已为用户 {username} ({chat_id}) 启动分析任务")
                else:
                    print(f"❌ 发送初始消息失败 (用户 {username}): {response.text}")
                    # 如果是用户阻止了 Bot，可以考虑取消订阅
                    if response.status_code == 403:
                        print(f"⚠️ 用户 {chat_id} 可能已阻止 Bot，考虑取消订阅")
                        # 可以选择自动取消订阅
                        # UserService.unsubscribe_user({"id": chat_id})
                    
            except Exception as e:
                print(f"❌ 推送失败 (用户 {username}): {str(e)}")
                
    except Exception as e:
        print(f"❌ 获取订阅用户失败: {str(e)}")

def start_scheduler():
    """启动定时任务调度器"""
    scheduler = BackgroundScheduler(executors=executors)
    
    # 添加定时任务
    # 每日上午9点推送（开盘前）
    scheduler.add_job(
        send_scheduled_report, 
        'cron', 
        hour=9, 
        minute=0,
        id='morning_report',
        name='Morning NASDAQ Report'
    )
    
    # 每日晚上8点推送（盘后分析）
    scheduler.add_job(
        send_scheduled_report, 
        'cron', 
        hour=20, 
        minute=0,
        id='evening_report',
        name='Evening NASDAQ Report'
    )
    
    scheduler.start()
    print("⏰ 定时任务调度器已启动")
    print("📅 推送时间: 每日 09:00 和 20:00")
    print("👥 使用数据库管理订阅用户")
    
    return scheduler

# 全局调度器实例
_scheduler = None

def get_scheduler():
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = start_scheduler()
    return _scheduler

def get_user_stats():
    """获取用户统计信息"""
    try:
        subscribed_users = UserService.list_subscribed_users()
        return {
            "subscribed_count": len(subscribed_users),
            "users": subscribed_users
        }
    except Exception as e:
        print(f"❌ 获取用户统计失败: {str(e)}")
        return {"subscribed_count": 0, "users": []}