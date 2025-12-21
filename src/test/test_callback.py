"""测试 step_callback 是否正常触发"""
from src.crew import NasdaqSummaryCrew
from dotenv import load_dotenv
from typing import Any

load_dotenv()

def test_callback():
    """测试回调函数"""
    
    # 创建一个测试回调
    step_count = [0]  # 使用列表来在闭包中修改值
    
    def test_step_callback(step_output: Any):
        step_count[0] += 1
        print(f"\n{'='*60}")
        print(f"🔔 回调触发 #{step_count[0]}")
        print(f"{'='*60}")
        
        # 打印对象类型
        step_type = type(step_output).__name__
        print(f"📊 对象类型: {step_type}")
        
        # 打印 step_output 对象的所有属性
        if hasattr(step_output, "__dict__"):
            print(f"\n📋 对象属性:")
            for key, value in step_output.__dict__.items():
                value_str = str(value)
                if len(value_str) > 200:
                    value_str = value_str[:200] + "..."
                print(f"  - {key}: {value_str}")
        else:
            print(f"📊 对象内容: {step_output}")
        
        # 根据类型提取关键信息
        print(f"\n🔍 关键信息:")
        
        if step_type == "ToolResult":
            print(f"  类型: 工具执行结果")
            tool = getattr(step_output, "tool", None)
            result = getattr(step_output, "result", None)
            if tool:
                print(f"  ✅ 工具名称: {tool}")
            if result:
                result_str = str(result)[:200] + "..." if len(str(result)) > 200 else str(result)
                print(f"  ✅ 执行结果: {result_str}")
        
        elif step_type == "AgentAction":
            print(f"  类型: Agent 动作")
            tool = getattr(step_output, "tool", None)
            tool_input = getattr(step_output, "tool_input", None)
            log = getattr(step_output, "log", None)
            
            if tool:
                print(f"  ✅ 调用工具: {tool}")
            if tool_input:
                input_str = str(tool_input)[:200] + "..." if len(str(tool_input)) > 200 else str(tool_input)
                print(f"  ✅ 工具输入: {input_str}")
            if log:
                log_str = log[:200] + "..." if len(log) > 200 else log
                print(f"  ✅ 思考日志: {log_str}")
        
        elif step_type == "AgentFinish":
            print(f"  类型: Agent 完成")
            return_values = getattr(step_output, "return_values", None)
            log = getattr(step_output, "log", None)
            
            if return_values:
                print(f"  ✅ 返回值: {return_values}")
            if log:
                log_str = log[:200] + "..." if len(log) > 200 else log
                print(f"  ✅ 完成日志: {log_str}")
        
        else:
            print(f"  类型: 未知类型 ({step_type})")
            # 尝试打印所有属性
            for attr in dir(step_output):
                if not attr.startswith("_"):
                    try:
                        value = getattr(step_output, attr)
                        if not callable(value):
                            value_str = str(value)[:100] + "..." if len(str(value)) > 100 else str(value)
                            print(f"  - {attr}: {value_str}")
                    except:
                        pass
        
        print(f"{'='*60}\n")
    
    # 创建 crew 并运行（不传入 chat_id，避免实际发送 Telegram 消息）
    print("🚀 开始测试 CrewAI 回调...")
    crew_instance = NasdaqSummaryCrew()
    crew = crew_instance.crew(step_callback=test_step_callback)
    
    try:
        result = crew.kickoff()
        print(f"\n✅ 任务完成！")
        print(f"📊 回调总共触发了 {step_count[0]} 次")
        print(f"\n📄 最终结果:\n{result.raw if hasattr(result, 'raw') else result}")
    except Exception as e:
        print(f"\n❌ 执行出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_callback()
