"""
代码审查智能体提示词模板
"""

# 系统提示词
CODE_REVIEW_SYSTEM_PROMPT = """
你是一位资深的代码审查专家。你的职责是：

## 1. 代码规范检查
- 命名规范（变量、函数、类、模块）
- 代码格式（缩进、空格、换行）
- 注释规范（文档字符串、行内注释）
- 导入规范（顺序、分组）

## 2. 代码质量评估
- 代码可读性
- 代码可维护性
- 代码复用性
- 代码复杂度

## 3. 安全漏洞扫描
- 输入验证
- SQL注入防护
- XSS防护
- 敏感数据泄露
- 认证授权问题

## 4. 性能分析
- 算法效率
- 数据结构选择
- 内存使用
- I/O操作优化

## 5. 重构建议
- 识别代码异味
- 提供重构方案
- 评估重构风险
- 优先级排序

## 6. 最佳实践
- 设计模式应用
- SOLID原则
- DRY原则
- KISS原则

## 审查标准
- **通过**：无严重和高优先级问题，评分 >= 80
- **需修改**：存在高优先级问题或评分 < 80
- **不通过**：存在严重问题或评分 < 60

你的输出必须是结构化的JSON格式。
"""

# 代码风格检查提示词
STYLE_CHECK_PROMPT = """
请检查以下代码的风格规范。

代码文件：
{code_file}

编程语言：{language}

请检查以下方面：
1. **命名规范**
   - 变量命名（snake_case/camelCase）
   - 函数命名
   - 类命名（PascalCase）
   - 常量命名（UPPER_CASE）

2. **代码格式**
   - 缩进一致性
   - 行长度限制
   - 空格使用
   - 换行规范

3. **注释规范**
   - 文档字符串
   - 行内注释
   - 注释质量

4. **导入规范**
   - 导入顺序
   - 分组组织
   - 避免通配符导入

请以JSON格式输出：
{{
    "issues": [
        {{
            "line_number": 10,
            "column": 1,
            "severity": "low/medium/high",
            "rule_id": "STYLE-001",
            "title": "问题标题",
            "description": "问题描述",
            "suggestion": "修改建议",
            "code_snippet": "问题代码"
        }}
    ],
    "metrics": {{
        "naming_convention_score": 85,
        "formatting_score": 90,
        "comment_score": 75,
        "import_score": 80
    }},
    "overall_style_score": 82
}}
"""

# 代码质量评估提示词
QUALITY_ASSESSMENT_PROMPT = """
请评估以下代码的质量。

代码文件：
{code_file}

编程语言：{language}

请评估以下方面：
1. **可读性**
   - 代码清晰度
   - 逻辑简洁性
   - 命名准确性

2. **可维护性**
   - 模块化程度
   - 耦合度
   - 内聚度

3. **可复用性**
   - 代码重复
   - 抽象程度
   - 接口设计

4. **复杂度**
   - 圈复杂度
   - 认知复杂度
   - 函数长度

请以JSON格式输出：
{{
    "issues": [
        {{
            "line_number": 25,
            "column": 1,
            "severity": "medium",
            "rule_id": "QUALITY-001",
            "title": "函数过长",
            "description": "函数超过50行，建议拆分",
            "suggestion": "将函数拆分为多个小函数",
            "code_snippet": "问题代码"
        }}
    ],
    "metrics": {{
        "readability_score": 80,
        "maintainability_score": 75,
        "reusability_score": 70,
        "cyclomatic_complexity": 12,
        "cognitive_complexity": 15
    }},
    "overall_quality_score": 76
}}
"""

# 安全扫描提示词
SECURITY_SCAN_PROMPT = """
请扫描以下代码的安全漏洞。

代码文件：
{code_file}

编程语言：{language}

请检查以下安全问题：
1. **输入验证**
   - 未验证的用户输入
   - SQL注入风险
   - 命令注入风险
   - 路径遍历风险

2. **认证授权**
   - 密码存储方式
   - Token安全性
   - 权限检查
   - 会话管理

3. **数据保护**
   - 敏感数据泄露
   - 日志中的敏感信息
   - 不安全的数据传输
   - 加密算法选择

4. **常见漏洞**
   - XSS漏洞
   - CSRF漏洞
   - SSRF漏洞
   - 不安全的反序列化

请以JSON格式输出：
{{
    "issues": [
        {{
            "line_number": 30,
            "column": 1,
            "severity": "critical/high/medium/low",
            "rule_id": "SEC-001",
            "title": "SQL注入风险",
            "description": "直接拼接SQL语句，存在注入风险",
            "suggestion": "使用参数化查询或ORM",
            "code_snippet": "问题代码",
            "cwe_id": "CWE-89"
        }}
    ],
    "vulnerabilities": [
        {{
            "type": "SQL Injection",
            "severity": "critical",
            "location": "文件:行号",
            "description": "漏洞描述",
            "remediation": "修复建议"
        }}
    ],
    "security_score": 65
}}
"""

# 性能分析提示词
PERFORMANCE_ANALYSIS_PROMPT = """
请分析以下代码的性能问题。

代码文件：
{code_file}

编程语言：{language}

请分析以下方面：
1. **算法效率**
   - 时间复杂度
   - 空间复杂度
   - 算法选择

2. **数据结构**
   - 数据结构选择
   - 内存使用
   - 访问模式

3. **I/O操作**
   - 文件I/O
   - 网络I/O
   - 数据库查询

4. **并发处理**
   - 线程安全
   - 锁竞争
   - 异步处理

请以JSON格式输出：
{{
    "issues": [
        {{
            "line_number": 45,
            "column": 1,
            "severity": "medium/high",
            "rule_id": "PERF-001",
            "title": "低效的循环",
            "description": "嵌套循环导致O(n²)复杂度",
            "suggestion": "使用字典或集合优化查找",
            "code_snippet": "问题代码"
        }}
    ],
    "performance_metrics": {{
        "time_complexity": "O(n²)",
        "space_complexity": "O(n)",
        "bottlenecks": ["循环内的数据库查询"],
        "optimization_opportunities": ["使用缓存", "批量处理"]
    }},
    "performance_score": 70
}}
"""

# 复杂度分析提示词
COMPLEXITY_ANALYSIS_PROMPT = """
请分析以下代码的复杂度。

代码文件：
{code_file}

编程语言：{language}

请分析以下复杂度：
1. **圈复杂度**
   - 分支语句数量
   - 循环语句数量
   - 条件表达式数量

2. **认知复杂度**
   - 嵌套深度
   - 逻辑复杂度
   - 理解难度

3. **结构复杂度**
   - 函数长度
   - 类大小
   - 模块耦合

请以JSON格式输出：
{{
    "issues": [
        {{
            "line_number": 20,
            "column": 1,
            "severity": "medium",
            "rule_id": "COMP-001",
            "title": "过高的圈复杂度",
            "description": "函数圈复杂度为15，超过建议值10",
            "suggestion": "拆分函数或使用策略模式",
            "code_snippet": "问题代码"
        }}
    ],
    "complexity_metrics": {{
        "cyclomatic_complexity": 15,
        "cognitive_complexity": 18,
        "max_nesting_depth": 4,
        "function_length": 80,
        "class_size": 500
    }},
    "complexity_score": 65
}}
"""

# 重构建议提示词
REFACTORING_SUGGESTION_PROMPT = """
请为以下代码提供重构建议。

代码文件：
{code_file}

已发现的问题：
{issues}

请提供：
1. **代码异味识别**
   - 重复代码
   - 过长函数
   - 过大类
   - 过多参数

2. **重构方案**
   - 提取方法
   - 提取类
   - 引入参数对象
   - 使用设计模式

3. **重构优先级**
   - 高优先级：影响安全或功能
   - 中优先级：影响可维护性
   - 低优先级：影响代码风格

请以JSON格式输出：
{{
    "refactoring_suggestions": [
        {{
            "id": "REF-001",
            "title": "提取用户验证逻辑",
            "description": "将用户验证逻辑提取到单独的类中",
            "priority": "high/medium/low",
            "effort": "small/medium/large",
            "impact": "high/medium/low",
            "before_code": "重构前代码",
            "after_code": "重构后代码",
            "benefits": ["提高可测试性", "降低耦合度"],
            "risks": ["需要更新测试用例"]
        }}
    ],
    "best_practices": [
        {{
            "category": "设计模式",
            "practice": "使用策略模式替代条件语句",
            "example": "示例代码",
            "benefit": "提高可扩展性"
        }}
    ]
}}
"""

# 审查决策提示词
REVIEW_DECISION_PROMPT = """
请根据以下审查结果做出审查决策。

审查结果：
{review_results}

评分：
- 总体评分：{overall_score}
- 代码质量：{code_quality_score}
- 安全评分：{security_score}
- 性能评分：{performance_score}

问题统计：
- 严重问题：{critical_issues}
- 高优先级：{high_issues}
- 中等优先级：{medium_issues}
- 低优先级：{low_issues}

审查标准：
- **通过**：无严重和高优先级问题，评分 >= 80
- **需修改**：存在高优先级问题或评分 < 80
- **不通过**：存在严重问题或评分 < 60

请以JSON格式输出：
{{
    "decision": "approved/needs_changes/rejected",
    "summary": "审查总结",
    "key_findings": [
        "主要发现1",
        "主要发现2"
    ],
    "action_items": [
        {{
            "priority": "critical/high/medium/low",
            "description": "需要修复的问题",
            "file": "文件路径",
            "line": "行号"
        }}
    ],
    "approval_conditions": [
        "修复所有严重问题",
        "提高测试覆盖率到80%"
    ],
    "review_notes": "审查备注"
}}
"""
