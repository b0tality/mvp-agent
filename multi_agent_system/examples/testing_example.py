"""
示例：使用软件测试智能体
"""

import asyncio
import json
from agents.testing import TestingAgent
from agents.code_review import CodeReviewAgent
from agents.mvp import MVPDeveloperAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本测试运行")
    print("=" * 60)
    
    # 创建智能体
    agent = TestingAgent({
        "model": "gpt-4",
        "temperature": 0.2
    })
    
    # 代码文件
    code_files = [
        {
            "path": "src/models/user.py",
            "language": "python",
            "content": """
class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password
    
    def check_password(self, password):
        return self.password == password
    
    def to_dict(self):
        return {
            "email": self.email,
            "created_at": self.created_at.isoformat()
        }
"""
        }
    ]
    
    # 项目信息
    project_info = {
        "api_design": {
            "endpoints": [
                {"path": "/users/register", "method": "POST", "description": "用户注册"},
                {"path": "/users/login", "method": "POST", "description": "用户登录"}
            ]
        },
        "security_design": {
            "authentication": {"method": "JWT"}
        },
        "data_models": {
            "users": {
                "fields": [
                    {"name": "email", "type": "string"},
                    {"name": "password", "type": "string"}
                ]
            }
        }
    }
    
    # 运行测试
    result = await agent.run_tests(code_files, project_info)
    
    # 输出结果
    print("\n测试结果:")
    print(f"状态: {result.get('status')}")
    print(f"单元测试通过率: {result.get('results', {}).get('unit_tests', {}).get('pass_rate', 0):.1f}%")
    print(f"集成测试通过率: {result.get('results', {}).get('integration_tests', {}).get('pass_rate', 0):.1f}%")
    print(f"总体覆盖率: {result.get('coverage', {}).get('overall', 0):.1f}%")
    print(f"缺陷数量: {len(result.get('bugs', []))}")
    
    return result


async def example_full_pipeline():
    """完整流程示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 完整流程（MVP开发 -> 代码审查 -> 测试）")
    print("=" * 60)
    
    # 步骤1: MVP开发
    print("\n步骤1: MVP开发...")
    mvp_agent = MVPDeveloperAgent({"model": "gpt-4"})
    
    technical_solution = {
        "tech_stack": {
            "backend": {"language": {"name": "Python"}, "web_framework": {"name": "FastAPI"}},
            "data_layer": {"primary_database": {"name": "PostgreSQL"}}
        },
        "api_design": {"endpoints": [{"path": "/users", "method": "POST"}]},
        "database_design": {"models": [{"name": "users", "fields": [{"name": "id", "type": "UUID"}]}]},
        "security_design": {"authentication": {"method": "JWT"}}
    }
    
    requirements = {"functional_requirements": [{"id": "FR-001", "title": "用户注册"}]}
    
    mvp_result = await mvp_agent.develop_mvp(technical_solution, requirements)
    
    if mvp_result.get("status") != "success":
        print(f"MVP开发失败: {mvp_result.get('error')}")
        return None
    
    print("MVP开发完成!")
    
    # 步骤2: 代码审查
    print("\n步骤2: 代码审查...")
    review_agent = CodeReviewAgent({"model": "gpt-4"})
    
    review_result = await review_agent.review_code(mvp_result.get("code_files", []))
    
    if review_result.get("status") != "success":
        print(f"代码审查失败: {review_result.get('error')}")
        return None
    
    print(f"代码审查完成! 评分: {review_result.get('overall_score', 0):.1f}")
    
    # 步骤3: 测试
    print("\n步骤3: 运行测试...")
    testing_agent = TestingAgent({"model": "gpt-4"})
    
    test_result = await testing_agent.run_tests(
        mvp_result.get("code_files", []),
        technical_solution
    )
    
    if test_result.get("status") == "success":
        print("\n测试完成!")
        print(f"单元测试通过率: {test_result.get('results', {}).get('unit_tests', {}).get('pass_rate', 0):.1f}%")
        print(f"总体覆盖率: {test_result.get('coverage', {}).get('overall', 0):.1f}%")
        print(f"缺陷数量: {len(test_result.get('bugs', []))}")
        
        return test_result
    else:
        print(f"测试失败: {test_result.get('error')}")
        return None


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - 软件测试智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_full_pipeline()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
