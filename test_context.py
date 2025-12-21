"""
测试任务context传递
"""
import platform
import signal

# Windows 平台兼容性修复
if platform.system() == "Windows":
    signal.SIGHUP = signal.SIGTERM
    signal.SIGTSTP = signal.SIGTERM
    signal.SIGQUIT = signal.SIGTERM
    signal.SIGUSR1 = signal.SIGTERM
    signal.SIGUSR2 = signal.SIGTERM
    signal.SIGCONT = signal.SIGTERM
    signal.SIGCHLD = signal.SIGTERM
    signal.SIGPIPE = signal.SIGTERM
    signal.SIGALRM = signal.SIGTERM
    signal.SIGTTIN = signal.SIGTERM
    signal.SIGTTOU = signal.SIGTERM

from src.crew import NasdaqSummaryCrew

def test_context():
    print("🧪 测试任务context传递...")
    
    crew_instance = NasdaqSummaryCrew()
    
    # 创建任务实例
    task1 = crew_instance.fetch_and_analyze_data_task()
    task2 = crew_instance.research_key_news_task()
    
    # 检查task3的context
    crew = crew_instance.crew()
    task3 = crew.tasks[2]
    
    print(f"\n✅ Task 1: {task1.description[:50]}...")
    print(f"✅ Task 2: {task2.description[:50]}...")
    print(f"✅ Task 3: {task3.description[:50]}...")
    print(f"\n📋 Task 3 的 context: {task3.context}")
    print(f"   - Context 包含 {len(task3.context)} 个任务")
    print(f"   - Context[0] == Task1: {task3.context[0] == task1}")
    print(f"   - Context[1] == Task2: {task3.context[1] == task2}")
    
    if len(task3.context) == 2:
        print("\n✅ Context 配置正确！")
    else:
        print("\n❌ Context 配置有问题！")

if __name__ == "__main__":
    test_context()
