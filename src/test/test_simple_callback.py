"""简单测试 - 验证回调是否触发"""
from crewai import Agent, Task, Crew
from dotenv import load_dotenv

load_dotenv()

def simple_test():
    """最简单的测试"""
    
    callback_triggered = [False]
    
    def my_callback(step_output):
        callback_triggered[0] = True
        print(f"\n✅ 回调触发！")
        print(f"   类型: {type(step_output).__name__}")
        if hasattr(step_output, "__dict__"):
            print(f"   属性: {step_output.__dict__}")
    
    # 创建一个简单的 agent 和 task
    agent = Agent(
        role="测试员",
        goal="完成测试",
        backstory="你是一个测试员",
        verbose=True
    )
    
    task = Task(
        description="说 'Hello World'",
        expected_output="一句问候",
        agent=agent
    )
    
    crew = Crew(
        agents=[agent],
        tasks=[task],
        verbose=True,
        step_callback=my_callback
    )
    
    print("🚀 开始测试...")
    result = crew.kickoff()
    
    print(f"\n📊 结果:")
    print(f"   回调是否触发: {callback_triggered[0]}")
    print(f"   任务结果: {result.raw if hasattr(result, 'raw') else result}")

if __name__ == "__main__":
    simple_test()
