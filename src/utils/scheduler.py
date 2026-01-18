# 定时任务处理
import os
import json
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.executors.pool import ThreadPoolExecutor
from src.utils.notifier import run_agent_and_notify
import requests
from datetime import datetime
from src.db.tg_user.user_service import UserService

# 从环境变量获取配置
TG_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TG_API_URL = f"https://api.telegram.org/bot{TG_TOKEN}"

# 用户数据文件
USERS_FILE = UserService.list_subscribed_users()

executors = {
    'default': ThreadPoolExecutor(10)
}

class UserManager:
    def __init__(self):
        self.users = {}  # {chat_id: user_info}
        self.load_users()
    
    def load_users(self):
        """加载用户数据"""
        try:
            if os.path.exists(USERS_FILE):
                with open(USERS_FILE, 'r', encoding='utf-8') as f:
                    self.users = json.load(f)
                # 转换 chat_id 为 int（JSON 中是字符串）
                self.users = {int(k): v for k, v in self.users.items()}
                print(f"📋 加载了 {len(self.users)} 个用户")
            else:
                self.users = {}
                print("📋 用户文件不存在，创建新的用户列表")
        except Exception as e:
            print(f"❌ 加载用户数据失败: {e}")
            self.users = {}
    
    def save_users(self):
        """保存用户数据"""
        try:
            # 转换 chat_id 为字符串（JSON 要求）
            users_to_save = {str(k): v for k, v in self.users.items()}
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users_to_save, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"❌ 保存用户数据失败: {e}")
    
    def add_or_update_user(self, chat_id: int, username: str = None, first_name: str = None):
        """添加或更新用户（任何与 Bot 互动的用户都会被记录）"""
        now = datetime.now().isoformat()
        
        if chat_id in self.users:
            # 更新现有用户的最后活跃时间
            self.users[chat_id].update({
                "username": username,
                "first_name": first_name,
                "last_active": now
            })
        else:
            # 新用户，默认订阅定时推送
            self.users[chat_id] = {
                "chat_id": chat_id,
                "username": username,
                "first_name": first_name,
                "first_interaction": now,
                "last_active": now,
                "subscribed": True,  # 默认订阅
                "active": True
            }
            print(f"✅ 新用户加入: {chat_id} ({username or first_name})")
        
        self.save_users()
    
    def unsubscribe_user(self, chat_id: int):
        """用户取消订阅"""
        if chat_id in self.users:
            self.users[chat_id]["subscribed"] = False
            self.save_users()
            print(f"❌ 用户取消订阅: {chat_id}")
            return True
        return False
    
    def subscribe_user(self, chat_id: int):
        """用户重新订阅"""
        if chat_id in self.users:
            self.users[chat_id]["subscribed"] = True
            self.save_users()
            print(f"✅ 用户重新订阅: {chat_id}")
            return True
        return False
    
    def get_subscribed_users(self):
        """获取所有订阅用户"""
        return [
            user for user in self.users.values() 
            if user.get("subscribed", True) and user.get("active", True)
        ]
    
    def deactivate_user(self, chat_id: int):
        """停用用户（发送失败时使用）"""
        if chat_id in self.users:
            self.users[chat_id]["active"] = False
            self.save_users()
            print(f"⚠️ 停用用户: {chat_id}")
    
    def get_user_count(self):
        """获取用户统计"""
        total = len(self.users)
        subscribed = len(self.get_subscribed_users())
        return {"total": total, "subscribed": subscribed}

# 全局用户管理器
user_manager = UserManager()

def send_scheduled_report():
    """发送定时报告给所有订阅用户"""
    subscribed_users = user_manager.get_subscribed_users()
    
    if not subscribed_users:
        print("⚠️ 没有订阅用户，跳过定时推送")
        return
    
    print(f"📅 开始定时推送，目标用户数: {len(subscribed_users)}")
    
    for user in subscribed_users:
        chat_id = user["chat_id"]
        username = user.get("username") or user.get("first_name", "用户")
        
        try:
            # 发送初始消息
            initial_msg = {
                "chat_id": chat_id,
                "text": f"📅 定时推送：正在生成纳斯达克100指数分析报告...\n\n💡 如不需要定时推送，请发送 /unsubscribe",
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
                # 如果是用户阻止了 Bot，停用该用户
                if response.status_code == 403:
                    user_manager.deactivate_user(chat_id)
                
        except Exception as e:
            print(f"❌ 推送失败 (用户 {username}): {str(e)}")

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
    print("👥 所有与 Bot 互动的用户都会自动接收推送")
    
    return scheduler

# 全局调度器实例
_scheduler = None

def get_scheduler():
    """获取调度器实例"""
    global _scheduler
    if _scheduler is None:
        _scheduler = start_scheduler()
    return _scheduler