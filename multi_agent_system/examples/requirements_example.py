"""
示例：使用需求分析智能体
"""

import asyncio
import json
from agents.requirements import RequirementsAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本需求分析")
    print("=" * 60)
    
    # 创建智能体
    agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    # 用户需求
    user_input = """
    我想开发一个在线商城系统，主要功能包括：
    1. 用户注册和登录
    2. 商品浏览和搜索
    3. 购物车功能
    4. 在线支付
    5. 订单管理
    """
    
    # 分析需求
    result = await agent.analyze_requirements(user_input)
    
    # 输出结果
    print("\n分析结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


async def example_with_clarification():
    """带澄清的需求分析示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 带澄清的需求分析")
    print("=" * 60)
    
    # 创建智能体
    agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    # 模糊的用户需求
    user_input = "我想要一个管理系统"
    
    # 分析需求
    result = await agent.analyze_requirements(user_input)
    
    # 检查是否需要澄清
    if result.get("status") == "needs_clarification":
        print("\n需要澄清:")
        print(json.dumps(result.get("clarification", {}), ensure_ascii=False, indent=2))
    else:
        print("\n分析结果:")
        print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


async def example_task_decomposition():
    """任务分解示例"""
    
    print("\n" + "=" * 60)
    print("示例3: 任务分解")
    print("=" * 60)
    
    # 创建智能体
    agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    # 用户需求
    user_input = """
    开发一个博客系统，功能包括：
    1. 用户认证
    2. 文章发布
    3. 评论系统
    4. 标签分类
    """
    
    # 分析需求
    analysis_result = await agent.analyze_requirements(user_input)
    
    if analysis_result.get("status") == "success":
        # 分解任务
        task_result = await agent.decompose_tasks()
        
        print("\n任务分解结果:")
        print(json.dumps(task_result, ensure_ascii=False, indent=2))
        
        return task_result
    
    return analysis_result


async def example_coordination():
    """协调示例"""
    
    print("\n" + "=" * 60)
    print("示例4: 智能体协调")
    print("=" * 60)
    
    # 创建智能体
    agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    # 用户需求
    user_input = "开发一个待办事项应用"
    
    # 分析需求
    analysis_result = await agent.analyze_requirements(user_input)
    
    if analysis_result.get("status") == "success":
        # 分解任务
        task_result = await agent.decompose_tasks()
        
        # 协调智能体
        tasks = task_result.get("tasks", [])
        coord_result = await agent.coordinate_agents(tasks)
        
        print("\n协调结果:")
        print(json.dumps(coord_result, ensure_ascii=False, indent=2))
        
        # 获取进度
        progress = await agent.get_progress()
        print("\n项目进度:")
        print(json.dumps(progress, ensure_ascii=False, indent=2))
        
        return coord_result
    
    return analysis_result


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - 需求分析智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_with_clarification()
    await example_task_decomposition()
    await example_coordination()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
