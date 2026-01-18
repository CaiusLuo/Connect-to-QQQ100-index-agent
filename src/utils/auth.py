"""权限管理模块"""
import os
from typing import Optional

# 从环境变量获取管理员用户ID
ADMIN_USER_ID = int(os.getenv("ADMIN_USER_ID", "0"))

def is_admin(user_id: int) -> bool:
    """检查用户是否为管理员"""
    return user_id == ADMIN_USER_ID

def check_admin_permission(user_id: int) -> tuple[bool, Optional[str]]:
    """
    检查管理员权限
    
    Returns:
        tuple: (是否有权限, 错误消息)
    """
    if not ADMIN_USER_ID:
        return False, "⚠️ 系统未配置管理员"
    
    if user_id != ADMIN_USER_ID:
        return False, "❌ 权限不足，只有管理员可以查看此信息"
    
    return True, None

def get_admin_commands() -> str:
    """获取管理员专用命令列表"""
    return """
🔧 管理员专用命令：
• /status 或 /状态 - 查看系统状态和用户统计
• /admin_help - 显示管理员帮助信息
    """

def get_admin_help() -> str:
    """获取管理员帮助信息"""
    return f"""
🛡️ 管理员控制面板

👤 当前管理员ID: {ADMIN_USER_ID}

📊 可用功能：
• 查看系统状态和用户统计
• 监控定时推送执行情况
• 查看数据库连接状态

📋 管理员命令：
• /status - 查看详细系统状态
• /admin_help - 显示此帮助信息

💡 提示：普通用户无法访问管理员功能
    """