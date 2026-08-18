"""
技术架构师提示词模板
"""

# 系统提示词
TECHNICAL_SYSTEM_PROMPT = """
你是一位资深的技术架构师。你的职责是：

## 1. 架构设计
- 设计可扩展的系统架构
- 选择合适的架构模式（微服务、单体、无服务器等）
- 定义组件边界和接口
- 设计数据流和通信机制

## 2. 技术选型
- 选择合适的技术栈
- 评估技术方案的优缺点
- 考虑团队技能和学习曲线
- 平衡创新与稳定性

## 3. 安全设计
- 设计认证和授权方案
- 制定数据保护策略
- 识别安全风险和威胁
- 制定安全最佳实践

## 4. 成本控制
- 估算基础设施成本
- 优化资源使用
- 设计弹性伸缩策略
- 控制运营成本

## 5. 文档输出
- 编写技术规格文档
- 记录架构决策
- 提供实施指南
- 制定技术标准

## 6. 设计原则
- 遵循SOLID原则
- 采用12因子应用方法论
- 考虑可维护性和可扩展性
- 平衡理想与现实

你的输出必须是结构化的JSON格式。
"""

# 架构设计提示词
ARCHITECTURE_DESIGN_PROMPT = """
根据以下需求，设计系统架构。

需求分析：
{requirements}

请设计：

1. **系统架构**
   - 架构模式（微服务/单体/无服务器/混合）
   - 核心组件划分
   - 组件间通信方式
   - 数据流设计

2. **组件设计**
   - 前端架构
   - 后端架构
   - 数据层架构
   - 基础设施层

3. **部署架构**
   - 部署环境
   - 容器化策略
   - 编排方案
   - 网络拓扑

请以JSON格式输出：
{{
    "system_architecture": {{
        "pattern": "架构模式",
        "description": "架构描述",
        "components": [
            {{
                "name": "组件名称",
                "type": "frontend/backend/database/infrastructure",
                "responsibility": "职责描述",
                "interfaces": ["接口列表"]
            }}
        ],
        "communication": {{
            "protocol": "通信协议",
            "pattern": "通信模式",
            "tools": ["工具列表"]
        }},
        "data_flow": [
            {{
                "from": "来源",
                "to": "目标",
                "data": "数据类型",
                "protocol": "协议"
            }}
        ]
    }},
    "component_design": {{
        "frontend": {{}},
        "backend": {{}},
        "data_layer": {{}},
        "infrastructure": {{}}
    }},
    "deployment_architecture": {{
        "environment": "环境",
        "containerization": "容器化策略",
        "orchestration": "编排方案",
        "network": {{}}
    }}
}}
"""

# 技术栈选择提示词
TECH_STACK_PROMPT = """
根据以下架构设计，选择合适的技术栈。

架构设计：
{architecture}

需求：
{requirements}

请为以下层次选择技术栈：

1. **前端**
   - 框架
   - UI库
   - 状态管理
   - 构建工具

2. **后端**
   - 编程语言
   - Web框架
   - API框架
   - 任务队列

3. **数据层**
   - 主数据库
   - 缓存数据库
   - 搜索引擎
   - 消息队列

4. **基础设施**
   - 云平台
   - 容器化
   - CI/CD
   - 监控

5. **安全**
   - 认证方案
   - 授权框架
   - 加密方案

请以JSON格式输出：
{{
    "frontend": {{
        "framework": {{
            "name": "框架名称",
            "version": "版本",
            "reason": "选择理由",
            "alternatives": ["替代方案"],
            "pros": ["优点"],
            "cons": ["缺点"]
        }},
        "ui_library": {{}},
        "state_management": {{}},
        "build_tools": {{}}
    }},
    "backend": {{
        "language": {{}},
        "web_framework": {{}},
        "api_framework": {{}},
        "task_queue": {{}}
    }},
    "data_layer": {{
        "primary_database": {{}},
        "cache": {{}},
        "search_engine": {{}},
        "message_queue": {{}}
    }},
    "infrastructure": {{
        "cloud_platform": {{}},
        "containerization": {{}},
        "orchestration": {{}},
        "ci_cd": {{}},
        "monitoring": {{}}
    }},
    "security": {{
        "authentication": {{}},
        "authorization": {{}},
        "encryption": {{}}
    }}
}}
"""

# API设计提示词
API_DESIGN_PROMPT = """
根据以下需求和技术栈，设计RESTful API。

需求：
{requirements}

技术栈：
{tech_stack}

请设计：

1. **API规范**
   - 命名规范
   - 版本控制
   - 响应格式
   - 错误处理

2. **API端点**
   - 资源定义
   - HTTP方法
   - URL路径
   - 请求/响应格式

3. **认证授权**
   - 认证方式
   - Token设计
   - 权限控制

4. **性能优化**
   - 分页策略
   - 缓存策略
   - 限流策略

请以JSON格式输出：
{{
    "api_specification": {{
        "version": "v1",
        "base_url": "/api/v1",
        "response_format": {{
            "success": true,
            "data": {{}},
            "error": null,
            "meta": {{}}
        }},
        "error_handling": {{
            "error_codes": {{}},
            "error_messages": {{}}
        }}
    }},
    "endpoints": [
        {{
            "path": "/resource",
            "method": "GET",
            "description": "描述",
            "authentication": true,
            "request": {{
                "params": {{}},
                "body": {{}},
                "headers": {{}}
            }},
            "response": {{
                "success": {{}},
                "error": {{}}
            }},
            "rate_limit": 100
        }}
    ],
    "authentication": {{
        "type": "JWT",
        "token_expiry": "24h",
        "refresh_token": true
    }},
    "pagination": {{
        "default_page_size": 20,
        "max_page_size": 100
    }}
}}
"""

# 数据库设计提示词
DATABASE_DESIGN_PROMPT = """
根据以下需求和API设计，设计数据库模式。

需求：
{requirements}

API设计：
{api_design}

请设计：

1. **数据库选型**
   - 主数据库类型
   - 缓存策略
   - 索引策略

2. **数据模型**
   - 实体定义
   - 关系设计
   - 字段规范

3. **数据迁移**
   - 迁移策略
   - 版本控制
   - 回滚方案

4. **性能优化**
   - 查询优化
   - 索引优化
   - 分区策略

请以JSON格式输出：
{{
    "database_type": "PostgreSQL/MySQL/MongoDB",
    "orm": "ORM框架",
    "models": [
        {{
            "name": "表名",
            "description": "描述",
            "fields": [
                {{
                    "name": "字段名",
                    "type": "数据类型",
                    "constraints": ["约束"],
                    "index": true/false
                }}
            ],
            "relationships": [
                {{
                    "type": "one_to_many/many_to_many/one_to_one",
                    "target": "关联表",
                    "foreign_key": "外键"
                }}
            ],
            "indexes": [
                {{
                    "name": "索引名",
                    "fields": ["字段"],
                    "type": "btree/hash/gin/gist"
                }}
            ]
        }}
    ],
    "migration_strategy": {{
        "tool": "迁移工具",
        "version_control": true,
        "rollback_support": true
    }},
    "optimization": {{
        "caching": "缓存策略",
        "query_optimization": "查询优化",
        "partitioning": "分区策略"
    }}
}}
"""

# 安全设计提示词
SECURITY_DESIGN_PROMPT = """
根据以下需求和架构，设计安全方案。

需求：
{requirements}

架构：
{architecture}

请设计：

1. **认证方案**
   - 认证方式
   - Token设计
   - 多因素认证
   - 会话管理

2. **授权方案**
   - 权限模型
   - 角色设计
   - 资源控制
   - 最小权限原则

3. **数据保护**
   - 传输加密
   - 存储加密
   - 数据脱敏
   - 备份策略

4. **安全防护**
   - 输入验证
   - SQL注入防护
   - XSS防护
   - CSRF防护

5. **合规性**
   - GDPR
   - 数据隐私
   - 审计日志

请以JSON格式输出：
{{
    "authentication": {{
        "method": "JWT/OAuth2/Session",
        "multi_factor": true/false,
        "token_design": {{
            "access_token_expiry": "15m",
            "refresh_token_expiry": "7d",
            "token_rotation": true
        }},
        "session_management": {{}}
    }},
    "authorization": {{
        "model": "RBAC/ABAC",
        "roles": [
            {{
                "name": "角色名",
                "permissions": ["权限列表"]
            }}
        ],
        "resource_control": {{}}
    }},
    "data_protection": {{
        "transport_encryption": "TLS 1.3",
        "storage_encryption": "AES-256",
        "data_masking": ["敏感字段"],
        "backup_strategy": {{}}
    }},
    "security_measures": {{
        "input_validation": true,
        "sql_injection_protection": true,
        "xss_protection": true,
        "csrf_protection": true,
        "rate_limiting": true
    }},
    "compliance": {{
        "gdpr": true/false,
        "data_privacy": {{}},
        "audit_logging": true
    }}
}}
"""

# 成本估算提示词
COST_ESTIMATION_PROMPT = """
根据以下技术方案，估算项目成本。

技术栈：
{tech_stack}

架构：
{architecture}

需求：
{requirements}

请估算：

1. **开发成本**
   - 人力成本
   - 开发工具
   - 培训成本

2. **基础设施成本**
   - 服务器
   - 存储
   - 网络
   - 第三方服务

3. **运营成本**
   - 维护成本
   - 监控成本
   - 支持成本

4. **扩展成本**
   - 扩容成本
   - 新功能开发
   - 技术升级

请以JSON格式输出：
{{
    "development_cost": {{
        "personnel": {{
            "frontend_developer": {{"count": 1, "monthly_cost": 0, "duration_months": 0}},
            "backend_developer": {{"count": 1, "monthly_cost": 0, "duration_months": 0}},
            "devops_engineer": {{"count": 1, "monthly_cost": 0, "duration_months": 0}},
            "total": 0
        }},
        "tools": {{
            "development_tools": 0,
            "testing_tools": 0,
            "total": 0
        }},
        "training": 0,
        "total": 0
    }},
    "infrastructure_cost": {{
        "compute": {{
            "servers": 0,
            "serverless": 0,
            "total": 0
        }},
        "storage": {{
            "database": 0,
            "file_storage": 0,
            "total": 0
        }},
        "network": {{
            "bandwidth": 0,
            "cdn": 0,
            "total": 0
        }},
        "third_party_services": {{
            "authentication": 0,
            "email": 0,
            "monitoring": 0,
            "total": 0
        }},
        "monthly_total": 0,
        "annual_total": 0
    }},
    "operational_cost": {{
        "maintenance": 0,
        "monitoring": 0,
        "support": 0,
        "monthly_total": 0,
        "annual_total": 0
    }},
    "scaling_cost": {{
        "horizontal_scaling": 0,
        "vertical_scaling": 0,
        "new_features": 0,
        "total": 0
    }},
    "total_cost": {{
        "development": 0,
        "infrastructure_annual": 0,
        "operational_annual": 0,
        "first_year_total": 0,
        "annual_recurring": 0
    }},
    "recommendations": [
        "成本优化建议"
    ]
}}
"""

# 架构决策记录提示词
ADR_PROMPT = """
记录以下架构决策。

决策标题：{title}
决策背景：{context}
决策内容：{decision}
决策后果：{consequences}
替代方案：{alternatives}

请以ADR（Architecture Decision Record）格式输出：
{{
    "id": "ADR-XXX",
    "title": "决策标题",
    "status": "proposed/accepted/deprecated/superseded",
    "context": "决策背景和问题描述",
    "decision": "决策内容",
    "consequences": {{
        "positive": ["积极影响"],
        "negative": ["消极影响"],
        "neutral": ["中性影响"]
    }},
    "alternatives": [
        {{
            "name": "替代方案",
            "pros": ["优点"],
            "cons": ["缺点"],
            "reason_rejected": "拒绝原因"
        }}
    ],
    "related_decisions": ["相关决策ID"],
    "date": "决策日期",
    "deciders": ["决策者"]
}}
"""
