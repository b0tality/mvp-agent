"""
MVP实现智能体提示词模板
"""

# 系统提示词
MVP_SYSTEM_PROMPT = """
你是一位资深的全栈开发工程师。你的职责是：

## 1. 代码生成
- 根据技术方案生成高质量代码
- 遵循编码规范和最佳实践
- 实现核心功能
- 处理边界情况和错误

## 2. 代码优化
- 优化代码性能
- 提高代码可读性
- 减少代码复杂度
- 消除代码重复

## 3. 测试编写
- 编写单元测试
- 编写集成测试
- 确保测试覆盖率
- 测试边界情况

## 4. 文档生成
- 生成README文档
- 编写API文档
- 添加代码注释
- 提供使用示例

## 5. 项目配置
- 配置依赖管理
- 设置构建脚本
- 配置开发环境
- 设置CI/CD

## 6. 开发原则
- DRY（Don't Repeat Yourself）
- KISS（Keep It Simple, Stupid）
- SOLID原则
- 测试驱动开发
- 代码可读性优先

你的输出必须是结构化的JSON格式。
"""

# 项目结构生成提示词
PROJECT_STRUCTURE_PROMPT = """
根据以下技术方案，生成项目结构。

技术方案：
{technical_solution}

需求：
{requirements}

请生成完整的项目目录结构，包括：
1. 源代码目录
2. 测试目录
3. 配置文件
4. 文档目录
5. 脚本目录

请以JSON格式输出：
{{
    "project_name": "项目名称",
    "project_structure": {{
        "root": {{
            "type": "directory",
            "children": [
                {{
                    "name": "src",
                    "type": "directory",
                    "description": "源代码目录",
                    "children": [...]
                }},
                {{
                    "name": "tests",
                    "type": "directory",
                    "description": "测试目录",
                    "children": [...]
                }},
                {{
                    "name": "docs",
                    "type": "directory",
                    "description": "文档目录"
                }},
                {{
                    "name": "scripts",
                    "type": "directory",
                    "description": "脚本目录"
                }}
            ]
        }}
    }},
    "files": [
        {{
            "path": "文件路径",
            "type": "file",
            "description": "文件描述"
        }}
    ]
}}
"""

# 代码生成提示词
CODE_GENERATION_PROMPT = """
根据以下信息生成代码文件。

技术方案：
{technical_solution}

项目结构：
{project_structure}

当前模块：{current_module}

请生成：
1. 模块代码
2. 相关配置
3. 依赖声明

代码要求：
- 遵循PEP8/ESLint等规范
- 添加必要的注释
- 处理错误和异常
- 使用类型注解
- 保持函数简洁

请以JSON格式输出：
{{
    "module_name": "模块名称",
    "files": [
        {{
            "path": "文件路径",
            "content": "文件内容",
            "language": "python/javascript/etc",
            "description": "文件描述"
        }}
    ],
    "dependencies": [
        {{
            "name": "依赖名称",
            "version": "版本",
            "category": "main/dev/test",
            "description": "依赖描述"
        }}
    ]
}}
"""

# 数据模型生成提示词
DATA_MODEL_PROMPT = """
根据以下数据库设计，生成数据模型代码。

数据库设计：
{database_design}

技术栈：
{tech_stack}

请生成：
1. 数据模型类
2. 数据库迁移
3. 模型验证
4. 模型关系

代码要求：
- 使用ORM框架
- 添加字段验证
- 定义模型关系
- 支持序列化

请以JSON格式输出：
{{
    "models": [
        {{
            "name": "模型名称",
            "file_path": "文件路径",
            "content": "模型代码",
            "description": "模型描述",
            "fields": [
                {{
                    "name": "字段名",
                    "type": "类型",
                    "constraints": ["约束"]
                }}
            ],
            "relationships": [
                {{
                    "type": "关系类型",
                    "target": "目标模型"
                }}
            ]
        }}
    ],
    "migrations": [
        {{
            "name": "迁移名称",
            "content": "迁移代码"
        }}
    ]
}}
"""

# API端点生成提示词
API_ENDPOINT_PROMPT = """
根据以下API设计，生成API端点代码。

API设计：
{api_design}

数据模型：
{data_models}

技术栈：
{tech_stack}

请生成：
1. API路由
2. 请求处理
3. 响应格式
4. 中间件
5. 验证逻辑

代码要求：
- 遵循RESTful规范
- 添加输入验证
- 处理错误响应
- 添加API文档
- 支持分页和过滤

请以JSON格式输出：
{{
    "endpoints": [
        {{
            "path": "端点路径",
            "method": "HTTP方法",
            "file_path": "文件路径",
            "content": "端点代码",
            "description": "端点描述",
            "request_schema": {{}},
            "response_schema": {{}},
            "authentication": true/false,
            "rate_limit": 100
        }}
    ],
    "middleware": [
        {{
            "name": "中间件名称",
            "content": "中间件代码"
        }}
    ],
    "validators": [
        {{
            "name": "验证器名称",
            "content": "验证器代码"
        }}
    ]
}}
"""

# 认证授权生成提示词
AUTH_GENERATION_PROMPT = """
根据以下安全设计，生成认证授权代码。

安全设计：
{security_design}

技术栈：
{tech_stack}

请生成：
1. 认证服务
2. 授权中间件
3. Token管理
4. 用户管理

代码要求：
- 实现JWT认证
- 支持刷新Token
- 实现RBAC授权
- 密码加密存储
- 防止暴力破解

请以JSON格式输出：
{{
    "auth_service": {{
        "file_path": "文件路径",
        "content": "服务代码",
        "description": "认证服务"
    }},
    "auth_middleware": {{
        "file_path": "文件路径",
        "content": "中间件代码",
        "description": "认证中间件"
    }},
    "token_manager": {{
        "file_path": "文件路径",
        "content": "管理器代码",
        "description": "Token管理"
    }},
    "user_service": {{
        "file_path": "文件路径",
        "content": "服务代码",
        "description": "用户服务"
    }}
}}
"""

# 测试生成提示词
TEST_GENERATION_PROMPT = """
为以下代码生成测试用例。

代码文件：
{code_files}

模块：{module_name}

请生成：
1. 单元测试
2. 集成测试
3. 边界测试
4. 错误测试

测试要求：
- 测试覆盖率 > 80%
- 测试独立性
- 测试可重复性
- 清晰的测试命名
- 测试数据准备

请以JSON格式输出：
{{
    "test_files": [
        {{
            "path": "测试文件路径",
            "content": "测试代码",
            "description": "测试描述",
            "test_cases": [
                {{
                    "id": "TC-001",
                    "name": "测试用例名称",
                    "description": "测试描述",
                    "type": "unit/integration/boundary/error",
                    "input": "输入数据",
                    "expected": "预期结果"
                }}
            ]
        }}
    ],
    "test_coverage": {{
        "target": 80,
        "modules": {{
            "module_name": "覆盖率"
        }}
    }}
}}
"""

# 文档生成提示词
DOCUMENTATION_PROMPT = """
为以下项目生成文档。

项目信息：
{project_info}

代码文件：
{code_files}

API设计：
{api_design}

请生成：
1. README文档
2. API文档
3. 开发指南
4. 部署指南

文档要求：
- 清晰的项目描述
- 安装和运行说明
- API使用示例
- 贡献指南
- 许可证信息

请以JSON格式输出：
{{
    "readme": {{
        "content": "README内容",
        "sections": [
            "项目介绍",
            "功能特性",
            "快速开始",
            "API文档",
            "开发指南",
            "部署指南",
            "贡献指南",
            "许可证"
        ]
    }},
    "api_docs": {{
        "content": "API文档内容",
        "format": "OpenAPI/Swagger"
    }},
    "developer_guide": {{
        "content": "开发指南内容"
    }},
    "deployment_guide": {{
        "content": "部署指南内容"
    }}
}}
"""

# Docker配置生成提示词
DOCKER_CONFIG_PROMPT = """
为以下项目生成Docker配置。

项目信息：
{project_info}

技术栈：
{tech_stack}

请生成：
1. Dockerfile
2. docker-compose.yml
3. .dockerignore
4. 环境变量配置

配置要求：
- 多阶段构建
- 最小化镜像
- 安全配置
- 健康检查
- 日志配置

请以JSON格式输出：
{{
    "dockerfile": {{
        "content": "Dockerfile内容",
        "description": "Docker构建文件"
    }},
    "docker_compose": {{
        "content": "docker-compose.yml内容",
        "description": "Docker编排文件"
    }},
    "dockerignore": {{
        "content": ".dockerignore内容",
        "description": "Docker忽略文件"
    }},
    "env_example": {{
        "content": ".env.example内容",
        "description": "环境变量示例"
    }}
}}
"""

# 代码优化提示词
CODE_OPTIMIZATION_PROMPT = """
优化以下代码。

代码文件：
{code_files}

优化目标：
{optimization_goals}

请进行：
1. 性能优化
2. 代码重构
3. 安全加固
4. 可读性提升

优化要求：
- 保持功能不变
- 提高代码质量
- 减少复杂度
- 消除重复代码

请以JSON格式输出：
{{
    "optimized_files": [
        {{
            "path": "文件路径",
            "original_content": "原始内容",
            "optimized_content": "优化后内容",
            "changes": [
                {{
                    "type": "performance/refactor/security/readability",
                    "description": "变更描述",
                    "impact": "影响说明"
                }}
            ]
        }}
    ],
    "optimization_report": {{
        "performance_improvement": "性能提升",
        "code_quality_score": "代码质量评分",
        "complexity_reduction": "复杂度降低",
        "issues_fixed": ["修复的问题"]
    }}
}}
"""
