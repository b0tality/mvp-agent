"""
示例：使用技术架构师智能体
"""

import asyncio
import json
from agents.technical import TechnicalAgent
from agents.requirements import RequirementsAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本技术方案设计")
    print("=" * 60)
    
    # 创建智能体
    agent = TechnicalAgent({
        "model": "gpt-4",
        "temperature": 0.2
    })
    
    # 模拟需求分析结果
    requirements = {
        "functional_requirements": [
            {
                "id": "FR-001",
                "title": "用户注册",
                "description": "用户可以通过邮箱或手机号注册账号",
                "priority": "must_have"
            },
            {
                "id": "FR-002",
                "title": "用户登录",
                "description": "用户可以使用账号密码登录系统",
                "priority": "must_have"
            },
            {
                "id": "FR-003",
                "title": "商品浏览",
                "description": "用户可以浏览商品列表和详情",
                "priority": "must_have"
            }
        ],
        "non_functional_requirements": [
            {
                "id": "NFR-001",
                "category": "性能",
                "description": "页面加载时间不超过3秒",
                "metric": "响应时间 < 3s"
            },
            {
                "id": "NFR-002",
                "category": "安全",
                "description": "用户密码加密存储",
                "metric": "使用bcrypt加密"
            }
        ],
        "constraints": [
            {
                "id": "CON-001",
                "description": "预算限制在10万以内",
                "impact": "选择成本效益高的技术栈"
            }
        ]
    }
    
    # 设计技术方案
    result = await agent.design_technical_solution(requirements)
    
    # 输出结果
    print("\n技术方案设计结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


async def example_with_requirements_analysis():
    """带需求分析的完整流程示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 完整流程（需求分析 -> 技术设计）")
    print("=" * 60)
    
    # 先进行需求分析
    req_agent = RequirementsAgent({
        "model": "gpt-4",
        "temperature": 0.3
    })
    
    user_input = """
    开发一个在线博客系统，功能包括：
    1. 用户注册和登录
    2. 文章发布和编辑
    3. 评论系统
    4. 标签分类
    5. 搜索功能
    """
    
    print("\n步骤1: 需求分析...")
    req_result = await req_agent.analyze_requirements(user_input)
    
    if req_result.get("status") != "success":
        print(f"需求分析失败: {req_result.get('error')}")
        return None
    
    print("需求分析完成!")
    
    # 进行技术设计
    tech_agent = TechnicalAgent({
        "model": "gpt-4",
        "temperature": 0.2
    })
    
    print("\n步骤2: 技术方案设计...")
    tech_result = await tech_agent.design_technical_solution(req_result["requirements"])
    
    if tech_result.get("status") == "success":
        print("\n技术方案设计完成!")
        
        # 显示架构
        print("\n系统架构:")
        architecture = tech_result.get("architecture", {}).get("system_architecture", {})
        print(f"  架构模式: {architecture.get('pattern', 'N/A')}")
        
        # 显示技术栈
        print("\n技术栈:")
        tech_stack = tech_result.get("tech_stack", {})
        for layer, details in tech_stack.items():
            if isinstance(details, dict) and details:
                print(f"  {layer}:")
                for key, value in details.items():
                    if isinstance(value, dict) and value.get("name"):
                        print(f"    - {key}: {value['name']}")
        
        # 显示API端点
        print("\nAPI端点:")
        endpoints = tech_result.get("api_design", {}).get("endpoints", [])
        for endpoint in endpoints[:5]:  # 只显示前5个
            print(f"  {endpoint.get('method', 'GET')} {endpoint.get('path', 'N/A')}")
        
        return tech_result
    else:
        print(f"技术方案设计失败: {tech_result.get('error')}")
        return None


async def example_create_adr():
    """创建架构决策记录示例"""
    
    print("\n" + "=" * 60)
    print("示例3: 创建架构决策记录")
    print("=" * 60)
    
    # 创建智能体
    agent = TechnicalAgent({
        "model": "gpt-4",
        "temperature": 0.2
    })
    
    # 创建ADR
    adr = await agent.create_adr(
        title="选择PostgreSQL作为主数据库",
        context="需要一个可靠的关系型数据库来存储用户数据和业务数据",
        decision="选择PostgreSQL作为主数据库",
        consequences="需要学习PostgreSQL的特性和优化技巧",
        alternatives=[
            {
                "name": "MySQL",
                "pros": ["广泛使用", "社区活跃"],
                "cons": ["功能相对较少"]
            },
            {
                "name": "MongoDB",
                "pros": ["灵活的schema", "易于扩展"],
                "cons": ["不适合复杂查询"]
            }
        ]
    )
    
    print("\n架构决策记录:")
    print(json.dumps(adr, ensure_ascii=False, indent=2))
    
    return adr


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - 技术架构师智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_with_requirements_analysis()
    await example_create_adr()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
