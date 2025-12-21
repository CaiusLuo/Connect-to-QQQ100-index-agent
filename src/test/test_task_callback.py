"""测试 task_callback 是否正常触发"""
from src.crew import NasdaqSummaryCrew
from dotenv import load_dotenv
from typing import Any

load_dotenv()

def test_task_callback():
    """测试任务回调函数"""
    
    task_count = [0]
    
    def my_task_callback(task_output: Any):
        task_count[0] += 1
        print(f"\n{'='*60}")
        print(f"✅ 任务回调触发 #{task_count[0]}")
        print(f"{'='*60}")
        
        # 打印对象类型
        task_type = type(task_output).__name__
        print(f"📊 对象类型: {task_type}")
        
        # 打印对象属性
        if hasattr(task_output, "__dict__"):
            print(f"\n📋 对象属性:")
            for key, value in task_output.__dict__.items():
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                print(f"  - {key}: {value_str}")
        
        # 提取关键信息
        print(f"\n🔍 关键信息:")
        
        description = getattr(task_output, "description", None)
        summary = getattr(task_output, "summary", None)
        raw = getattr(task_output, "raw", None)
        
        if description:
            print(f"  ✅ 描述: {description[:100]}...")
        if summary:
            print(f"  ✅ 摘要: {summary[:100]}...")
        if raw:
            print(f"  ✅ 原始输出: {str(raw)[:200]}...")
        
        print(f"{'='*60}\n")
    
    # 创建 crew 并运行
    print("🚀 开始测试 CrewAI 任务回调...")
    crew_instance = NasdaqSummaryCrew()
    crew = crew_instance.crew(task_callback=my_task_callback)
    
    try:
        result = crew.kickoff()
        print(f"\n✅ 任务完成！")
        print(f"📊 任务回调总共触发了 {task_count[0]} 次")
        print(f"\n📄 最终结果:\n{result.raw if hasattr(result, 'raw') else result}")
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_task_callback()
