"""
需求分析智能体提示词模板
"""

# 系统提示词
REQUIREMENTS_SYSTEM_PROMPT = """
你是一位资深的需求分析师兼项目主管。你的职责是：

## 1. 需求分析
- 理解用户的业务需求
- 识别功能需求和非功能需求
- 发现潜在的隐含需求
- 评估需求的可行性和风险

## 2. 项目协调
- 分解任务并分配给专业智能体
- 监控项目进度
- 处理异常情况
- 确保交付质量

## 3. 输出规范
- 使用标准的用户故事格式
- 提供明确的验收标准
- 给出合理的优先级排序

## 4. 工作原则
- 主动澄清模糊需求
- 识别需求间的依赖关系
- 评估技术可行性
- 考虑非功能需求（性能、安全、可用性）
- 记录所有假设和约束

你的输出必须是结构化的JSON格式。
"""

# 需求解析提示词
REQUIREMENT_PARSING_PROMPT = """
请分析以下用户需求，提取：

1. **功能需求**（Functional Requirements）- 系统必须做什么
2. **非功能需求**（Non-Functional Requirements）- 系统如何运行（性能、安全、可用性等）
3. **约束条件**（Constraints）- 限制条件
4. **假设条件**（Assumptions）- 需要确认的前提
5. **风险点**（Risks）- 潜在风险

用户需求：
{user_input}

请以JSON格式输出：
{{
    "functional_requirements": [
        {{
            "id": "FR-XXX",
            "title": "需求标题",
            "description": "详细描述",
            "priority": "must_have/should_have/could_have/wont_have"
        }}
    ],
    "non_functional_requirements": [
        {{
            "id": "NFR-XXX",
            "category": "性能/安全/可用性/可维护性",
            "description": "详细描述",
            "metric": "量化指标"
        }}
    ],
    "constraints": [
        {{
            "id": "CON-XXX",
            "description": "约束描述",
            "impact": "影响说明"
        }}
    ],
    "assumptions": [
        {{
            "id": "ASM-XXX",
            "description": "假设描述",
            "risk": "如果不成立的风险"
        }}
    ],
    "risks": [
        {{
            "id": "RSK-XXX",
            "description": "风险描述",
            "probability": "high/medium/low",
            "impact": "high/medium/low",
            "mitigation": "缓解措施"
        }}
    ]
}}
"""

# 用户故事生成提示词
USER_STORY_PROMPT = """
根据以下需求，生成标准的用户故事。

需求列表：
{requirements}

用户故事格式：
- 作为<角色>，我想要<功能>，以便<价值>

请以JSON格式输出：
{{
    "user_stories": [
        {{
            "id": "US-XXX",
            "role": "用户角色",
            "feature": "功能描述",
            "benefit": "业务价值",
            "acceptance_criteria": [
                "验收标准1",
                "验收标准2"
            ],
            "priority": "must_have/should_have/could_have/wont_have",
            "story_points": 1/2/3/5/8/13
        }}
    ]
}}
"""

# 验收标准生成提示词
ACCEPTANCE_CRITERIA_PROMPT = """
为以下用户故事生成详细的验收标准。

用户故事：
{user_story}

验收标准应满足INVEST原则：
- Independent（独立的）
- Negotiable（可协商的）
- Valuable（有价值的）
- Estimable（可估算的）
- Small（小的）
- Testable（可测试的）

请以JSON格式输出：
{{
    "acceptance_criteria": [
        {{
            "id": "AC-XXX",
            "description": "验收标准描述",
            "given": "前置条件",
            "when": "操作",
            "then": "预期结果",
            "test_cases": [
                {{
                    "id": "TC-XXX",
                    "description": "测试用例描述",
                    "input": "输入",
                    "expected_output": "预期输出"
                }}
            ]
        }}
    ]
}}
"""

# 优先级排序提示词
PRIORITIZATION_PROMPT = """
使用MoSCoW方法对以下需求进行优先级排序。

需求列表：
{requirements}

MoSCoW方法：
- **Must Have**：必须有，没有则系统无法运行
- **Should Have**：应该有，重要但不是关键
- **Could Have**：可以有，锦上添花
- **Won't Have**：不会有，本次迭代不包含

请以JSON格式输出：
{{
    "priority_matrix": {{
        "must_have": [
            {{
                "id": "REQ-XXX",
                "title": "需求标题",
                "reason": "排序理由"
            }}
        ],
        "should_have": [...],
        "could_have": [...],
        "wont_have": [...]
    }},
    "dependencies": [
        {{
            "from": "REQ-XXX",
            "to": "REQ-YYY",
            "type": "blocks/blocked_by/related"
        }}
    ],
    "estimated_effort": {{
        "total_story_points": 0,
        "estimated_sprints": 0
    }}
}}
"""

# 协调任务分解提示词
TASK_DECOMPOSITION_PROMPT = """
根据以下需求分析结果，分解任务并分配给合适的智能体。

需求分析结果：
{requirements_analysis}

可用智能体：
1. technical_architect - 技术架构师：负责技术方案设计
2. mvp_developer - MVP开发者：负责核心功能实现
3. code_reviewer - 代码审查员：负责代码质量审查
4. tester - 测试工程师：负责测试执行
5. deployer - 部署工程师：负责部署配置

请以JSON格式输出：
{{
    "tasks": [
        {{
            "id": "TASK-XXX",
            "title": "任务标题",
            "description": "任务描述",
            "assigned_to": "智能体名称",
            "dependencies": ["依赖的任务ID"],
            "estimated_time": "预估时间",
            "priority": "high/medium/low",
            "deliverables": ["交付物列表"]
        }}
    ],
    "execution_order": ["TASK-001", "TASK-002", ...],
    "parallel_tasks": [["TASK-001", "TASK-002"], ...]
}}
"""

# 问题澄清提示词
CLARIFICATION_PROMPT = """
我需要澄清以下问题以更好地理解需求：

当前需求分析：
{current_analysis}

需要澄清的问题：
{questions}

请以友好的方式向用户提问，并说明为什么需要这些信息。

输出格式：
{{
    "clarification_needed": true,
    "questions": [
        {{
            "id": "Q-XXX",
            "question": "问题描述",
            "reason": "为什么需要澄清",
            "suggested_answers": ["可能的答案1", "可能的答案2"]
        }}
    ],
    "message": "给用户的友好提示信息"
}}
"""
