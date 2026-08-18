"""
软件测试智能体提示词模板
"""

# 系统提示词
TESTING_SYSTEM_PROMPT = """
你是一位资深的软件测试工程师。你的职责是：

## 1. 单元测试
- 编写和执行单元测试
- 测试单个函数和方法
- 验证边界条件
- 测试异常处理

## 2. 集成测试
- 测试模块间交互
- 测试API端点
- 测试数据库操作
- 测试外部服务集成

## 3. 端到端测试
- 测试完整用户流程
- 模拟用户操作
- 验证业务逻辑
- 测试UI交互

## 4. 性能测试
- 负载测试
- 压力测试
- 并发测试
- 响应时间测试

## 5. 安全测试
- 漏洞扫描
- 渗透测试
- 认证授权测试
- 数据安全测试

## 6. 测试报告
- 生成测试报告
- 统计测试结果
- 分析测试覆盖率
- 记录缺陷

## 测试原则
- 测试独立性
- 测试可重复性
- 测试自验证性
- 测试及时性
- 测试全面性

你的输出必须是结构化的JSON格式。
"""

# 单元测试生成提示词
UNIT_TEST_PROMPT = """
请为以下代码生成单元测试。

代码文件：
{code_file}

编程语言：{language}

请生成全面的单元测试：
1. **正常流程测试**
   - 正常输入
   - 预期输出
   - 边界值

2. **异常流程测试**
   - 无效输入
   - 异常处理
   - 错误恢复

3. **边界条件测试**
   - 最小值
   - 最大值
   - 空值
   - 特殊字符

测试要求：
- 使用测试框架（pytest/jest等）
- 清晰的测试命名
- 测试数据准备
- 断言明确
- 覆盖率 > 80%

请以JSON格式输出：
{{
    "test_file": {{
        "path": "测试文件路径",
        "content": "测试代码",
        "language": "python/javascript"
    }},
    "test_cases": [
        {{
            "id": "TC-001",
            "name": "测试用例名称",
            "description": "测试描述",
            "type": "normal/boundary/exception",
            "function": "被测函数",
            "input": "输入数据",
            "expected": "预期结果",
            "assertions": ["断言列表"]
        }}
    ],
    "coverage_target": {{
        "line": 80,
        "branch": 70,
        "function": 90
    }}
}}
"""

# 集成测试生成提示词
INTEGRATION_TEST_PROMPT = """
请为以下API和模块生成集成测试。

API设计：
{api_design}

模块依赖：
{module_dependencies}

请生成集成测试：
1. **API端点测试**
   - 请求格式
   - 响应格式
   - 状态码
   - 错误处理

2. **数据库集成测试**
   - CRUD操作
   - 事务处理
   - 数据一致性

3. **服务集成测试**
   - 服务间调用
   - 超时处理
   - 重试机制

测试要求：
- 测试环境隔离
- 数据准备和清理
- Mock外部依赖
- 异步测试支持

请以JSON格式输出：
{{
    "test_file": {{
        "path": "测试文件路径",
        "content": "测试代码"
    }},
    "test_cases": [
        {{
            "id": "IT-001",
            "name": "测试用例名称",
            "description": "测试描述",
            "type": "api/database/service",
            "endpoint": "API端点",
            "method": "HTTP方法",
            "request": {{}},
            "expected_response": {{}},
            "setup": "测试准备",
            "teardown": "测试清理"
        }}
    ]
}}
"""

# 性能测试生成提示词
PERFORMANCE_TEST_PROMPT = """
请为以下系统生成性能测试方案。

系统信息：
{system_info}

API端点：
{api_endpoints}

请生成性能测试：
1. **负载测试**
   - 正常负载
   - 峰值负载
   - 持续负载

2. **压力测试**
   - 超出极限
   - 恢复能力
   - 资源使用

3. **并发测试**
   - 多用户并发
   - 竞争条件
   - 死锁检测

测试指标：
- 响应时间（平均、P95、P99）
- 吞吐量（请求/秒）
- 错误率
- 资源使用率

请以JSON格式输出：
{{
    "test_scenarios": [
        {{
            "id": "PT-001",
            "name": "场景名称",
            "description": "场景描述",
            "type": "load/stress/concurrent",
            "duration": "测试时长",
            "users": "并发用户数",
            "ramp_up": "爬坡时间",
            "endpoints": [
                {{
                    "path": "端点路径",
                    "method": "HTTP方法",
                    "weight": "权重"
                }}
            ],
            "thresholds": {{
                "response_time_p95": "阈值",
                "error_rate": "阈值",
                "throughput": "阈值"
            }}
        }}
    ],
    "test_script": {{
        "tool": "locust/jmeter/k6",
        "content": "测试脚本"
    }}
}}
"""

# 安全测试生成提示词
SECURITY_TEST_PROMPT = """
请为以下系统生成安全测试方案。

系统信息：
{system_info}

安全设计：
{security_design}

请生成安全测试：
1. **认证测试**
   - 登录安全
   - 密码策略
   - 会话管理
   - Token安全

2. **授权测试**
   - 权限检查
   - 越权访问
   - 角色验证

3. **输入验证测试**
   - SQL注入
   - XSS攻击
   - 命令注入
   - 路径遍历

4. **数据安全测试**
   - 敏感数据保护
   - 传输加密
   - 存储加密

请以JSON格式输出：
{{
    "test_cases": [
        {{
            "id": "ST-001",
            "name": "测试用例名称",
            "description": "测试描述",
            "type": "auth/authz/input/data",
            "category": "测试类别",
            "severity": "critical/high/medium/low",
            "steps": ["测试步骤"],
            "expected": "预期结果",
            "tools": ["测试工具"]
        }}
    ],
    "vulnerability_scans": [
        {{
            "tool": "扫描工具",
            "target": "扫描目标",
            "config": {{}}
        }}
    ]
}}
"""

# 测试报告生成提示词
TEST_REPORT_PROMPT = """
请根据以下测试结果生成测试报告。

测试结果：
{test_results}

覆盖率数据：
{coverage_data}

缺陷列表：
{bugs}

请生成测试报告：
1. **测试概述**
   - 测试范围
   - 测试环境
   - 测试时间

2. **测试结果**
   - 测试统计
   - 通过率
   - 覆盖率

3. **缺陷分析**
   - 缺陷统计
   - 严重程度分布
   - 缺陷趋势

4. **质量评估**
   - 代码质量
   - 系统稳定性
   - 性能表现

5. **建议和结论**
   - 改进建议
   - 发布建议
   - 风险评估

请以JSON格式输出：
{{
    "report": {{
        "title": "测试报告标题",
        "generated_at": "生成时间",
        "summary": {{
            "total_tests": 0,
            "passed": 0,
            "failed": 0,
            "skipped": 0,
            "pass_rate": "通过率",
            "coverage": "覆盖率"
        }},
        "sections": [
            {{
                "title": "章节标题",
                "content": "章节内容"
            }}
        ],
        "recommendations": ["建议列表"],
        "conclusion": "结论",
        "release_recommendation": "发布建议"
    }}
}}
"""

# 测试数据生成提示词
TEST_DATA_PROMPT = """
请为以下测试用例生成测试数据。

测试用例：
{test_cases}

数据模型：
{data_models}

请生成测试数据：
1. **正常数据**
   - 有效输入
   - 典型值
   - 边界值

2. **异常数据**
   - 无效输入
   - 超出范围
   - 格式错误

3. **边界数据**
   - 最小值
   - 最大值
   - 空值
   - 特殊字符

请以JSON格式输出：
{{
    "test_data": [
        {{
            "id": "TD-001",
            "test_case_id": "TC-001",
            "type": "normal/boundary/invalid",
            "data": {{}},
            "description": "数据描述"
        }}
    ],
    "fixtures": [
        {{
            "name": "fixture名称",
            "description": "fixture描述",
            "setup": "设置代码",
            "teardown": "清理代码"
        }}
    ]
}}
"""
