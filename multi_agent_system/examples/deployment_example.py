"""
示例：使用软件部署智能体
"""

import asyncio
import json
from agents.deployment import DeploymentAgent
from agents.testing import TestingAgent
from agents.mvp import MVPDeveloperAgent


async def example_basic_usage():
    """基本使用示例"""
    
    print("=" * 60)
    print("示例1: 基本部署规划")
    print("=" * 60)
    
    # 创建智能体
    agent = DeploymentAgent({
        "model": "gpt-4",
        "temperature": 0.2
    })
    
    # 代码文件
    code_files = [
        {
            "path": "src/main.py",
            "language": "python",
            "content": """
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Hello World"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
"""
        }
    ]
    
    # 技术方案
    technical_solution = {
        "tech_stack": {
            "backend": {
                "language": {"name": "Python", "version": "3.11"},
                "web_framework": {"name": "FastAPI"}
            },
            "data_layer": {
                "primary_database": {"name": "PostgreSQL"},
                "cache": {"name": "Redis"}
            }
        },
        "system_architecture": {
            "pattern": "微服务架构"
        }
    }
    
    # 测试结果
    test_results = {
        "status": "success",
        "pass_rate": 95.0,
        "coverage": 85.0
    }
    
    # 规划部署
    result = await agent.plan_deployment(
        code_files,
        technical_solution,
        test_results
    )
    
    # 输出结果
    print("\n部署规划结果:")
    print(f"状态: {result.get('status')}")
    print(f"部署策略: {result.get('deployment_plan', {}).get('deployment_strategy', {}).get('type', 'N/A')}")
    print(f"环境数量: {len(result.get('deployment_plan', {}).get('environments', {}))}")
    
    return result


async def example_full_pipeline():
    """完整流程示例"""
    
    print("\n" + "=" * 60)
    print("示例2: 完整流程（MVP开发 -> 测试 -> 部署）")
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
    
    # 步骤2: 测试
    print("\n步骤2: 运行测试...")
    testing_agent = TestingAgent({"model": "gpt-4"})
    
    test_result = await testing_agent.run_tests(
        mvp_result.get("code_files", []),
        technical_solution
    )
    
    if test_result.get("status") != "success":
        print(f"测试失败: {test_result.get('error')}")
        return None
    
    print(f"测试完成! 通过率: {test_result.get('results', {}).get('overall', {}).get('pass_rate', 0):.1f}%")
    
    # 步骤3: 部署规划
    print("\n步骤3: 部署规划...")
    deployment_agent = DeploymentAgent({"model": "gpt-4"})
    
    deploy_result = await deployment_agent.plan_deployment(
        mvp_result.get("code_files", []),
        technical_solution,
        test_result
    )
    
    if deploy_result.get("status") == "success":
        print("\n部署规划完成!")
        print(f"部署策略: {deploy_result.get('deployment_plan', {}).get('deployment_strategy', {}).get('type', 'N/A')}")
        
        # 显示Docker配置
        print("\nDocker配置:")
        docker_config = deploy_result.get("docker_config", {})
        print(f"  Dockerfile: {'已生成' if docker_config.get('dockerfile', {}).get('content') else '未生成'}")
        print(f"  docker-compose: {'已生成' if docker_config.get('docker_compose', {}).get('content') else '未生成'}")
        
        # 显示Kubernetes配置
        print("\nKubernetes配置:")
        k8s_config = deploy_result.get("kubernetes_config", {})
        print(f"  Deployment: {'已生成' if k8s_config.get('deployment', {}).get('content') else '未生成'}")
        print(f"  Service: {'已生成' if k8s_config.get('service', {}).get('content') else '未生成'}")
        
        return deploy_result
    else:
        print(f"部署规划失败: {deploy_result.get('error')}")
        return None


async def main():
    """主函数"""
    
    print("多智能体应用开发系统 - 软件部署智能体示例")
    print("=" * 60)
    
    # 运行示例
    await example_basic_usage()
    await example_full_pipeline()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
