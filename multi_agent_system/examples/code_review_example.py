"""
示例：使用代码审查智能体
"""

import asyncio
import json
from agents.code_review import CodeReviewAgent
from agents.mvp import MVPDeveloperAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本代码审查")
    print("=" * 60)
    
    # 创建智能体
    agent = CodeReviewAgent({
        "model": "gpt-4",
        "temperature": 0.1
    })
    
    # 代码文件
    code_files = [
        {
            "path": "src/models/user.py",
            "language": "python",
            "content": """
from datetime import datetime

class User:
    def __init__(self, email, password):
        self.email = email
        self.password = password
        self.created_at = datetime.now()
    
    def check_password(self, password):
        return self.password == password
    
    def to_dict(self):
        return {
            "email": self.email,
            "password": self.password,
            "created_at": self.created_at.isoformat()
        }
"""
        },
        {
            "path": "src/api/users.py",
            "language": "python",
            "content": """
from fastapi import APIRouter, HTTPException
from src.models.user import User

router = APIRouter()

users_db = []

@router.post("/users/register")
async def register_user(email: str, password: str):
    # 检查用户是否存在
    for user in users_db:
        if user.email == email:
            raise HTTPException(status_code=400, detail="用户已存在")
    
    # 创建用户
    user = User(email, password)
    users_db.append(user)
    
    return {"message": "注册成功"}

@router.post("/users/login")
async def login_user(email: str, password: str):
    for user in users_db:
        if user.email == email and user.check_password(password):
            return {"message": "登录成功"}
    
    raise HTTPException(status_code=401, detail="用户名或密码错误")
"""
        }
    ]
    
    # 审查代码
    result = await agent.review_code(code_files)
    
    # 输出结果
    print("\n代码审查结果:")
    print(f"状态: {result.get('status')}")
    print(f"是否通过: {result.get('approved')}")
    print(f"总体评分: {result.get('overall_score')}")
    print(f"问题总数: {result.get('issues_summary', {}).get('total')}")
    
    # 显示严重问题
    print("\n严重问题:")
    for issue in result.get("issues", []):
        if issue.get("severity") in ["critical", "high"]:
            print(f"  [{issue.get('severity')}] {issue.get('file_path')}:{issue.get('line_number')}")
            print(f"    {issue.get('title')}: {issue.get('description')}")
    
    return result


async def example_with_mvp_development():
    """带MVP开发的完整流程示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 完整流程（MVP开发 -> 代码审查）")
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
    
    if review_result.get("status") == "success":
        print("\n代码审查完成!")
        print(f"是否通过: {review_result.get('approved')}")
        print(f"总体评分: {review_result.get('overall_score')}")
        
        # 显示重构建议
        print("\n重构建议:")
        for suggestion in review_result.get("refactoring_suggestions", [])[:3]:
            print(f"  - {suggestion.get('title')}: {suggestion.get('description')}")
        
        return review_result
    else:
        print(f"代码审查失败: {review_result.get('error')}")
        return None


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - 代码审查智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_with_mvp_development()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
