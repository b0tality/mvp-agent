# 智能体1：需求分析（主管节点）- 实现方案

## 1. 角色定位

### 1.1 双重职责
- **需求分析师**：解析用户需求，生成结构化文档
- **主管节点**：协调其他智能体，监控项目进度

### 1.2 核心能力
- 自然语言理解与解析
- 需求结构化与优先级排序
- 用户故事生成
- 验收标准定义
- 智能体协调与调度
- 进度监控与异常处理

---

## 2. 技术架构

### 2.1 模块结构

```
agents/requirements/
├── __init__.py
├── agent.py              # 主智能体类
├── prompts.py            # 提示词模板
├── tools/
│   ├── __init__.py
│   ├── requirement_parser.py    # 需求解析工具
│   ├── user_story_generator.py # 用户故事生成
│   ├── acceptance_criteria.py  # 验收标准生成
│   ├── priority_calculator.py  # 优先级计算
│   └── coordinator.py          # 协调器工具
├── state.py              # 状态定义
└── README.md             # 本文档
```

### 2.2 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| LLM | OpenAI GPT-4 | 推理和生成 |
| 框架 | LangChain | 智能体编排 |
| 状态管理 | LangGraph State | 状态同步 |
| 输出格式 | JSON | 结构化数据 |

---

## 3. 状态定义

```python
class RequirementsState(TypedDict):
    # 输入
    user_input: str                    # 用户原始输入
    
    # 解析结果
    functional_requirements: list      # 功能需求列表
    non_functional_requirements: list  # 非功能需求列表
    constraints: list                  # 约束条件
    assumptions: list                  # 假设条件
    
    # 结构化输出
    user_stories: list                 # 用户故事
    acceptance_criteria: list          # 验收标准
    priority_matrix: dict              # 优先级矩阵
    
    # 协调状态
    current_phase: str                 # 当前阶段
    assigned_agents: dict              # 已分配的智能体
    progress: dict                     # 进度跟踪
    decisions: list                    # 决策记录
    
    # 元数据
    status: str                        # 分析状态
    created_at: str                    # 创建时间
    updated_at: str                    # 更新时间
    errors: list                       # 错误记录
```

---

## 4. 核心工具实现

### 4.1 需求解析器

```python
class RequirementParserTool(BaseTool):
    """解析用户自然语言需求"""
    
    name = "requirement_parser"
    description = "解析用户需求，提取功能和非功能需求"
    
    def _run(self, user_input: str) -> dict:
        # 1. 识别需求类型
        # 2. 提取关键实体
        # 3. 识别关系和依赖
        # 4. 输出结构化需求
        pass
```

### 4.2 用户故事生成器

```python
class UserStoryGeneratorTool(BaseTool):
    """生成标准用户故事"""
    
    name = "user_story_generator"
    description = "根据需求生成用户故事格式的描述"
    
    # 格式：作为<角色>，我想要<功能>，以便<价值>
    def _run(self, requirements: list) -> list:
        pass
```

### 4.3 协调器

```python
class CoordinatorTool(BaseTool):
    """协调其他智能体"""
    
    name = "coordinator"
    description = "分配任务给其他智能体并跟踪进度"
    
    def _run(self, action: str, target_agent: str, task: dict) -> dict:
        # 分配任务
        # 跟踪进度
        # 处理异常
        pass
```

---

## 5. 工作流程

### 5.1 需求分析流程

```
用户输入
    │
    ▼
┌─────────────────┐
│  输入预处理     │ ── 清理、标准化
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  需求解析       │ ── 提取功能/非功能需求
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  用户故事生成   │ ── 转换为用户故事
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  验收标准定义   │ ── 生成验收标准
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  优先级排序     │ ── MoSCoW方法
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  输出结构化文档 │ ── JSON格式
└─────────────────┘
```

### 5.2 主管协调流程

```
需求分析完成
    │
    ▼
┌─────────────────┐
│  任务分解       │ ── WBS分解
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  智能体分配     │ ── 根据能力分配
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  进度监控       │ ── 实时跟踪
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  异常处理       │ ── 错误恢复
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  质量把关       │ ── 输出验证
└─────────────────┘
```

---

## 6. 提示词设计

### 6.1 系统提示词

```python
REQUIREMENTS_SYSTEM_PROMPT = """
你是一位资深的需求分析师兼项目主管。你的职责是：

1. **需求分析**
   - 理解用户的业务需求
   - 识别功能需求和非功能需求
   - 发现潜在的隐含需求
   - 评估需求的可行性和风险

2. **项目协调**
   - 分解任务并分配给专业智能体
   - 监控项目进度
   - 处理异常情况
   - 确保交付质量

3. **输出规范**
   - 使用标准的用户故事格式
   - 提供明确的验收标准
   - 给出合理的优先级排序

你的输出必须是结构化的JSON格式。
"""
```

### 6.2 需求解析提示词

```python
REQUIREMENT_PARSING_PROMPT = """
请分析以下用户需求，提取：

1. 功能需求（Functional Requirements）
2. 非功能需求（Non-Functional Requirements）
3. 约束条件（Constraints）
4. 假设条件（Assumptions）
5. 风险点（Risks）

用户需求：
{user_input}

请以JSON格式输出：
{
    "functional_requirements": [...],
    "non_functional_requirements": [...],
    "constraints": [...],
    "assumptions": [...],
    "risks": [...]
}
"""
```

---

## 7. 代码实现

### 7.1 主智能体类

```python
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

class RequirementsAgent:
    """需求分析智能体（兼任主管节点）"""
    
    def __init__(self, config: dict):
        self.llm = ChatOpenAI(
            model=config.get("model", "gpt-4"),
            temperature=config.get("temperature", 0.3)
        )
        self.tools = self._init_tools()
        self.agent = self._create_agent()
        self.state = RequirementsStateManager()
    
    def _init_tools(self) -> list:
        """初始化工具集"""
        return [
            RequirementParserTool(),
            UserStoryGeneratorTool(),
            AcceptanceCriteriaTool(),
            PriorityCalculatorTool(),
            CoordinatorTool()
        ]
    
    def _create_agent(self) -> AgentExecutor:
        """创建智能体"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", REQUIREMENTS_SYSTEM_PROMPT),
            ("human", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        agent = create_openai_tools_agent(self.llm, self.tools, prompt)
        return AgentExecutor(agent=agent, tools=self.tools, verbose=True)
    
    async def analyze_requirements(self, user_input: str) -> dict:
        """分析用户需求"""
        # 更新状态
        self.state.update("user_input", user_input)
        self.state.update("status", "analyzing")
        
        # 执行分析
        result = await self.agent.ainvoke({"input": user_input})
        
        # 更新状态
        self.state.update("functional_requirements", result["functional"])
        self.state.update("non_functional_requirements", result["non_functional"])
        self.state.update("status", "completed")
        
        return result
    
    async def coordinate_agents(self, tasks: list) -> dict:
        """协调其他智能体"""
        assignments = {}
        
        for task in tasks:
            # 根据任务类型分配智能体
            agent = self._assign_agent(task)
            assignments[agent] = task
            
            # 分配任务
            await self._dispatch_task(agent, task)
        
        # 监控进度
        progress = await self._monitor_progress(assignments)
        
        return progress
```

### 7.2 状态管理器

```python
class RequirementsStateManager:
    """需求状态管理器"""
    
    def __init__(self):
        self._state = {
            "user_input": "",
            "functional_requirements": [],
            "non_functional_requirements": [],
            "user_stories": [],
            "acceptance_criteria": [],
            "priority_matrix": {},
            "current_phase": "idle",
            "assigned_agents": {},
            "progress": {},
            "status": "initialized",
            "errors": []
        }
        self._history = []
    
    def update(self, key: str, value: any):
        """更新状态"""
        self._history.append({
            "timestamp": datetime.now().isoformat(),
            "key": key,
            "old_value": self._state.get(key),
            "new_value": value
        })
        self._state[key] = value
    
    def get(self, key: str) -> any:
        """获取状态值"""
        return self._state.get(key)
    
    def get_all(self) -> dict:
        """获取完整状态"""
        return self._state.copy()
    
    def get_history(self) -> list:
        """获取变更历史"""
        return self._history
```

---

## 8. 使用示例

### 8.1 基本使用

```python
import asyncio
from agents.requirements.agent import RequirementsAgent

async def main():
    # 初始化智能体
    config = {
        "model": "gpt-4",
        "temperature": 0.3
    }
    agent = RequirementsAgent(config)
    
    # 分析需求
    user_input = """
    我想开发一个在线商城系统，主要功能包括：
    1. 用户注册和登录
    2. 商品浏览和搜索
    3. 购物车功能
    4. 在线支付
    5. 订单管理
    """
    
    result = await agent.analyze_requirements(user_input)
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
```

### 8.2 输出示例

```json
{
    "functional_requirements": [
        {
            "id": "FR-001",
            "title": "用户注册",
            "description": "用户可以通过邮箱或手机号注册账号",
            "priority": "Must Have"
        },
        {
            "id": "FR-002",
            "title": "用户登录",
            "description": "用户可以使用账号密码登录系统",
            "priority": "Must Have"
        }
    ],
    "non_functional_requirements": [
        {
            "id": "NFR-001",
            "category": "性能",
            "description": "页面加载时间不超过3秒",
            "metric": "响应时间 < 3s"
        }
    ],
    "user_stories": [
        {
            "id": "US-001",
            "story": "作为新用户，我想要注册账号，以便使用商城服务",
            "acceptance_criteria": [
                "支持邮箱注册",
                "支持手机号注册",
                "密码强度验证"
            ]
        }
    ],
    "priority_matrix": {
        "must_have": ["FR-001", "FR-002", "FR-003"],
        "should_have": ["FR-004", "FR-005"],
        "could_have": ["FR-006"],
        "wont_have": ["FR-007"]
    }
}
```

---

## 9. 测试策略

### 9.1 单元测试

```python
import pytest
from agents.requirements.agent import RequirementsAgent

@pytest.mark.asyncio
async def test_analyze_requirements():
    agent = RequirementsAgent({"model": "gpt-4"})
    result = await agent.analyze_requirements("开发一个博客系统")
    
    assert "functional_requirements" in result
    assert len(result["functional_requirements"]) > 0
```

### 9.2 集成测试

```python
@pytest.mark.asyncio
async def test_coordinate_agents():
    agent = RequirementsAgent({"model": "gpt-4"})
    
    # 模拟任务分配
    tasks = [
        {"type": "technical_design", "description": "设计系统架构"},
        {"type": "implementation", "description": "实现核心功能"}
    ]
    
    result = await agent.coordinate_agents(tasks)
    assert "assignments" in result
```

---

## 10. 后续优化

### 10.1 短期优化
- [ ] 添加更多需求解析规则
- [ ] 支持多轮对话澄清需求
- [ ] 优化提示词提高准确性

### 10.2 中期优化
- [ ] 添加需求模板库
- [ ] 支持历史项目学习
- [ ] 实现需求变更管理

### 10.3 长期优化
- [ ] 添加自然语言生成能力
- [ ] 支持多语言需求
- [ ] 实现需求自动验证

---

*文档版本：1.0*
*最后更新：2026-08-17*
