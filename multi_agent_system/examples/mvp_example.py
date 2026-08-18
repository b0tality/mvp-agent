"""
示例：使用MVP实现智能体
"""

import asyncio
import json
from agents.mvp import MVPDeveloperAgent
from agents.technical import TechnicalAgent
from agents.requirements import RequirementsAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本MVP开发")
    print("=" * 60)
    
    # 创建智能体
    agent = MVPDeveloperAgent({
        "model": "gpt-4",
        "temperature": 0.4
    })
    
    # 模拟技术方案
    technical_solution = {
        "system_architecture": {
            "pattern": "单体架构",
            "components": [
                {
                    "name": "Web服务",
                    "type": "backend",
                    "responsibility": "处理HTTP请求"
                }
            ]
        },
        "tech_stack": {
            "backend": {
                "language": {"name": "Python", "version": "3.11+"},
                "web_framework": {"name": "FastAPI", "reason": "高性能"}
            },
            "data_layer": {
                "primary_database": {"name": "PostgreSQL", "reason": "ACID支持"}
            }
        },
        "api_design": {
            "api_specification": {
                "version": "v1",
                "base_url": "/api/v1"
            },
            "endpoints": [
                {
                    "path": "/users/register",
                    "method": "POST",
                    "description": "用户注册"
                },
                {
                    "path": "/users/login",
                    "method": "POST",
                    "description": "用户登录"
                }
            ]
        },
        "database_design": {
            "database_type": "PostgreSQL",
            "models": [
                {
                    "name": "users",
                    "fields": [
                        {"name": "id", "type": "UUID"},
                        {"name": "email", "type": "VARCHAR(255)"},
                        {"name": "password_hash", "type": "VARCHAR(255)"}
                    ]
                }
            ]
        },
        "security_design": {
            "authentication": {
                "method": "JWT",
                "token_design": {
                    "access_token_expiry": "15m",
                    "refresh_token_expiry": "7d"
                }
            }
        }
    }
    
    # 模拟需求
    requirements = {
        "functional_requirements": [
            {"id": "FR-001", "title": "用户注册", "description": "用户可以通过邮箱注册"},
            {"id": "FR-002", "title": "用户登录", "description": "用户可以登录系统"}
        ]
    }
    
    # 开发MVP
    result = await agent.develop_mvp(technical_solution, requirements)
    
    # 输出结果
    print("\nMVP开发结果:")
    print(f"状态: {result.get('status')}")
    print(f"项目名称: {result.get('project_name')}")
    print(f"代码文件数: {len(result.get('code_files', []))}")
    print(f"测试文件数: {len(result.get('test_files', []))}")
    print(f"进度: {result.get('progress')}%")
    
    return result


async def example_full_pipeline():
    """完整流程示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 完整流程（需求分析 -> 技术设计 -> MVP开发）")
    print("=" * 60)
    
    # 步骤1: 需求分析
    print("\n步骤1: 需求分析...")
    req_agent = RequirementsAgent({"model": "gpt-4"})
    
    user_input = """
    开发一个简单的待办事项应用，功能包括：
    1. 用户注册和登录
    2. 创建待办事项
    3. 标记完成
    4. 删除待办
    """
    
    req_result = await req_agent.analyze_requirements(user_input)
    
    if req_result.get("status") != "success":
        print(f"需求分析失败: {req_result.get('error')}")
        return None
    
    print("需求分析完成!")
    
    # 步骤2: 技术设计
    print("\n步骤2: 技术设计...")
    tech_agent = TechnicalAgent({"model": "gpt-4"})
    
    tech_result = await tech_agent.design_technical_solution(req_result["requirements"])
    
    if tech_result.get("status") != "success":
        print(f"技术设计失败: {tech_result.get('error')}")
        return None
    
    print("技术设计完成!")
    
    # 步骤3: MVP开发
    print("\n步骤3: MVP开发...")
    mvp_agent = MVPDeveloperAgent({"model": "gpt-4"})
    
    mvp_result = await mvp_agent.develop_mvp(
        tech_result,
        req_result["requirements"]
    )
    
    if mvp_result.get("status") == "success":
        print("\nMVP开发完成!")
        print(f"项目名称: {mvp_result.get('project_name')}")
        print(f"代码文件数: {len(mvp_result.get('code_files', []))}")
        print(f"测试文件数: {len(mvp_result.get('test_files', []))}")
        
        # 显示部分代码文件
        print("\n生成的代码文件:")
        for file in mvp_result.get("code_files", [])[:5]:
            print(f"  - {file.get('path')}: {file.get('description')}")
        
        return mvp_result
    else:
        print(f"MVP开发失败: {mvp_result.get('error')}")
        return None


async def example_optimize_code():
    """代码优化示例"""
    
    print("\n" + "=" * 60)
    print("示例3: 代码优化")
    print("=" * 60)
    
    # 创建智能体
    agent = MVPDeveloperAgent({"model": "gpt-4"})
    
    # 模拟已有代码文件
    agent.state_manager.add_code_file({
        "path": "src/models/user.py",
        "content": """
class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def check_password(self, password):
        return self.password == password
""",
        "language": "python",
        "description": "用户模型"
    })
    
    # 优化代码
    result = await agent.optimize_code(["performance", "security", "readability"])
    
    print("\n代码优化结果:")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - MVP实现智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_full_pipeline()
    await example_optimize_code()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
