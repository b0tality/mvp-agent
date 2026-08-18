"""
软件部署智能体提示词模板
"""

# 系统提示词
DEPLOYMENT_SYSTEM_PROMPT = """
你是一位资深的DevOps工程师。你的职责是：

## 1. 部署方案设计
- 选择部署策略（滚动、蓝绿、金丝雀）
- 设计基础设施架构
- 规划环境配置
- 制定回滚方案

## 2. 容器化配置
- 编写Dockerfile
- 配置docker-compose
- 优化镜像大小
- 管理容器生命周期

## 3. CI/CD配置
- 配置持续集成
- 配置持续部署
- 自动化测试集成
- 代码质量检查

## 4. 监控配置
- 配置指标监控
- 配置日志收集
- 配置告警规则
- 配置链路追踪

## 5. 安全配置
- 配置SSL/TLS
- 配置防火墙
- 配置密钥管理
- 配置访问控制

## 6. 成本优化
- 资源使用优化
- 成本估算
- 扩缩容策略
- 预留实例建议

## 部署原则
- 自动化优先
- 不可变基础设施
- 基础设施即代码
- 持续交付
- 快速回滚

你的输出必须是结构化的JSON格式。
"""

# 部署方案设计提示词
DEPLOYMENT_PLAN_PROMPT = """
请根据以下信息设计部署方案。

技术方案：
{technical_solution}

项目信息：
{project_info}

测试结果：
{test_results}

请设计完整的部署方案：
1. **部署策略选择**
   - 滚动部署（Rolling Update）
   - 蓝绿部署（Blue-Green）
   - 金丝雀部署（Canary）
   - 重新部署（Recreate）

2. **环境规划**
   - 开发环境（Development）
   - 预发布环境（Staging）
   - 生产环境（Production）

3. **基础设施规划**
   - 云服务提供商
   - 服务器规格
   - 网络架构
   - 存储方案

4. **高可用设计**
   - 负载均衡
   - 自动扩缩容
   - 故障转移
   - 数据备份

请以JSON格式输出：
{{
    "deployment_strategy": {{
        "type": "rolling/blue_green/canary/recreate",
        "reason": "选择理由",
        "rollback_strategy": "回滚策略"
    }},
    "environments": {{
        "development": {{
            "url": "开发环境URL",
            "resources": {{}},
            "purpose": "用途说明"
        }},
        "staging": {{
            "url": "预发布环境URL",
            "resources": {{}},
            "purpose": "用途说明"
        }},
        "production": {{
            "url": "生产环境URL",
            "resources": {{}},
            "purpose": "用途说明"
        }}
    }},
    "infrastructure": {{
        "provider": "aws/azure/gcp/aliyun",
        "region": "区域",
        "compute": {{
            "instance_type": "实例类型",
            "instances": "实例数量",
            "auto_scaling": true/false
        }},
        "storage": {{
            "database": "数据库配置",
            "cache": "缓存配置",
            "file_storage": "文件存储配置"
        }},
        "networking": {{
            "vpc": "VPC配置",
            "subnets": ["子网配置"],
            "load_balancer": "负载均衡配置"
        }}
    }},
    "high_availability": {{
        "load_balancing": "负载均衡策略",
        "auto_scaling": "自动扩缩容策略",
        "failover": "故障转移策略",
        "backup": "备份策略"
    }}
}}
"""

# Docker配置生成提示词
DOCKER_CONFIG_PROMPT = """
请为以下项目生成Docker配置。

项目信息：
{project_info}

技术栈：
{tech_stack}

请生成：
1. **Dockerfile**
   - 多阶段构建
   - 最小化镜像
   - 安全配置
   - 健康检查

2. **docker-compose.yml**
   - 服务定义
   - 网络配置
   - 卷挂载
   - 环境变量

3. **.dockerignore**
   - 忽略不必要的文件

4. **环境变量配置**
   - .env.example

请以JSON格式输出：
{{
    "dockerfile": {{
        "content": "Dockerfile内容",
        "stages": ["build", "runtime"],
        "base_images": ["基础镜像列表"]
    }},
    "docker_compose": {{
        "content": "docker-compose.yml内容",
        "services": ["服务列表"],
        "networks": ["网络列表"],
        "volumes": ["卷列表"]
    }},
    "dockerignore": {{
        "content": ".dockerignore内容"
    }},
    "env_example": {{
        "content": ".env.example内容",
        "variables": ["环境变量列表"]
    }}
}}
"""

# Kubernetes配置提示词
KUBERNETES_CONFIG_PROMPT = """
请为以下项目生成Kubernetes配置。

项目信息：
{project_info}

Docker配置：
{docker_config}

请生成：
1. **Deployment**
   - 副本数
   - 资源限制
   - 健康检查
   - 滚动更新策略

2. **Service**
   - 服务类型
   - 端口映射
   - 选择器

3. **Ingress**
   - 域名配置
   - SSL终止
   - 路由规则

4. **ConfigMap/Secret**
   - 配置管理
   - 密钥管理

5. **HPA**
   - 自动扩缩容配置

请以JSON格式输出：
{{
    "deployment": {{
        "content": "Deployment YAML",
        "replicas": 3,
        "resources": {{
            "requests": {{"cpu": "100m", "memory": "128Mi"}},
            "limits": {{"cpu": "500m", "memory": "512Mi"}}
        }}
    }},
    "service": {{
        "content": "Service YAML",
        "type": "ClusterIP/NodePort/LoadBalancer",
        "ports": [{{"port": 80, "targetPort": 8080}}]
    }},
    "ingress": {{
        "content": "Ingress YAML",
        "host": "example.com",
        "tls": true
    }},
    "configmap": {{
        "content": "ConfigMap YAML",
        "data": {{}}
    }},
    "secret": {{
        "content": "Secret YAML",
        "data": {{}}
    }},
    "hpa": {{
        "content": "HPA YAML",
        "min_replicas": 2,
        "max_replicas": 10,
        "target_cpu": 80
    }}
}}
"""

# CI/CD配置提示词
CICD_CONFIG_PROMPT = """
请为以下项目生成CI/CD配置。

项目信息：
{project_info}

部署配置：
{deployment_config}

请生成：
1. **CI配置（持续集成）**
   - 代码检查
   - 单元测试
   - 集成测试
   - 代码覆盖率
   - 安全扫描

2. **CD配置（持续部署）**
   - 构建镜像
   - 推送镜像
   - 部署到环境
   - 回滚机制

3. **流水线阶段**
   - 构建阶段
   - 测试阶段
   - 部署阶段

请以JSON格式输出：
{{
    "ci_config": {{
        "provider": "github_actions/gitlab_ci/jenkins",
        "content": "CI配置内容",
        "stages": [
            {{
                "name": "lint",
                "description": "代码检查",
                "commands": ["命令列表"]
            }},
            {{
                "name": "test",
                "description": "运行测试",
                "commands": ["命令列表"]
            }}
        ]
    }},
    "cd_config": {{
        "content": "CD配置内容",
        "stages": [
            {{
                "name": "build",
                "description": "构建镜像",
                "commands": ["命令列表"]
            }},
            {{
                "name": "deploy",
                "description": "部署应用",
                "commands": ["命令列表"]
            }}
        ]
    }},
    "pipeline": {{
        "stages": ["lint", "test", "build", "deploy"],
        "triggers": {{
            "push": "main/develop",
            "pull_request": "main"
        }}
    }}
}}
"""

# 监控配置提示词
MONITORING_CONFIG_PROMPT = """
请为以下系统配置监控方案。

系统信息：
{system_info}

部署配置：
{deployment_config}

请配置：
1. **指标监控（Metrics）**
   - 系统指标（CPU、内存、磁盘）
   - 应用指标（请求量、响应时间、错误率）
   - 业务指标（用户数、订单量）

2. **日志监控（Logging）**
   - 日志收集
   - 日志存储
   - 日志查询
   - 日志告警

3. **链路追踪（Tracing）**
   - 请求追踪
   - 性能分析
   - 依赖分析

4. **告警配置（Alerting）**
   - 告警规则
   - 通知渠道
   - 告警升级

请以JSON格式输出：
{{
    "metrics": {{
        "tool": "prometheus/grafana",
        "content": "Prometheus配置",
        "dashboards": ["仪表板列表"],
        "exporters": ["导出器列表"]
    }},
    "logging": {{
        "tool": "elk/loki",
        "content": "日志配置",
        "retention": "保留策略",
        "queries": ["常用查询"]
    }},
    "tracing": {{
        "tool": "jaeger/zipkin",
        "content": "追踪配置",
        "sampling_rate": "采样率"
    }},
    "alerting": {{
        "rules": [
            {{
                "name": "规则名称",
                "condition": "触发条件",
                "severity": "严重程度",
                "notification": "通知渠道"
            }}
        ],
        "channels": ["通知渠道列表"]
    }}
}}
"""

# 部署文档生成提示词
DEPLOYMENT_DOCS_PROMPT = """
请根据以下部署配置生成部署文档。

部署配置：
{deployment_config}

运维信息：
{operations_info}

请生成：
1. **部署指南**
   - 环境准备
   - 部署步骤
   - 验证方法

2. **运维手册**
   - 日常运维
   - 故障处理
   - 扩缩容操作

3. **回滚指南**
   - 回滚条件
   - 回滚步骤
   - 数据恢复

4. **安全指南**
   - 安全配置
   - 密钥管理
   - 访问控制

请以JSON格式输出：
{{
    "deployment_guide": {{
        "content": "部署指南内容",
        "sections": [
            "环境准备",
            "部署步骤",
            "验证方法"
        ]
    }},
    "operations_manual": {{
        "content": "运维手册内容",
        "sections": [
            "日常运维",
            "故障处理",
            "扩缩容操作"
        ]
    }},
    "rollback_guide": {{
        "content": "回滚指南内容",
        "sections": [
            "回滚条件",
            "回滚步骤",
            "数据恢复"
        ]
    }},
    "security_guide": {{
        "content": "安全指南内容",
        "sections": [
            "安全配置",
            "密钥管理",
            "访问控制"
        ]
    }}
}}
"""

# 成本估算提示词
COST_ESTIMATION_PROMPT = """
请根据以下部署配置估算成本。

部署配置：
{deployment_config}

资源需求：
{resource_requirements}

请估算：
1. **基础设施成本**
   - 计算资源
   - 存储资源
   - 网络资源

2. **服务成本**
   - 托管服务
   - 数据库服务
   - 缓存服务

3. **运维成本**
   - 监控服务
   - 日志服务
   - 备份服务

4. **优化建议**
   - 资源优化
   - 成本优化
   - 预留实例

请以JSON格式输出：
{{
    "infrastructure_cost": {{
        "compute": {{
            "instance_type": "实例类型",
            "quantity": 3,
            "monthly_cost": 300,
            "annual_cost": 3600
        }},
        "storage": {{
            "database": 100,
            "cache": 50,
            "file_storage": 30
        }},
        "network": {{
            "bandwidth": 50,
            "load_balancer": 20
        }}
    }},
    "service_cost": {{
        "managed_services": 200,
        "monitoring": 50,
        "logging": 30
    }},
    "total_monthly": 830,
    "total_annual": 9960,
    "optimization_suggestions": [
        {{
            "category": "计算资源",
            "suggestion": "使用预留实例",
            "potential_savings": "30%"
        }},
        {{
            "category": "存储",
            "suggestion": "使用冷热分层存储",
            "potential_savings": "20%"
        }}
    ]
}}
"""
