"""
代码审查智能体主类
负责代码质量审查、安全扫描、性能分析和重构建议
"""

from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain.agents import create_agent
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

from .state import CodeReviewState, CodeReviewStateManager
from .prompts import (
    CODE_REVIEW_SYSTEM_PROMPT,
    STYLE_CHECK_PROMPT,
    QUALITY_ASSESSMENT_PROMPT,
    SECURITY_SCAN_PROMPT,
    PERFORMANCE_ANALYSIS_PROMPT,
    COMPLEXITY_ANALYSIS_PROMPT,
    REFACTORING_SUGGESTION_PROMPT,
    REVIEW_DECISION_PROMPT
)
from .tools import (
    StyleCheckerTool,
    QualityAssessorTool,
    SecurityScannerTool,
    PerformanceAnalyzerTool,
    ComplexityAnalyzerTool,
    RefactoringAdvisorTool
)


class CodeReviewAgent:
    """
    代码审查智能体
    
    职责：
    1. 代码规范检查
    2. 代码质量评估
    3. 安全漏洞扫描
    4. 性能分析
    5. 复杂度分析
    6. 重构建议
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化代码审查智能体
        
        Args:
            config: 配置参数
                - model: 模型名称，默认 mimo
                - temperature: 温度参数，默认 0.1
                - max_tokens: 最大token数，默认 4000
                - api_key: API密钥
                - base_url: API基础URL（用于本地LLM）
        """
        self.config = config or {}
        
        # 初始化LLM（支持本地LLM）
        llm_kwargs = {
            "model": self.config.get("model", "mimo"),
            "temperature": self.config.get("temperature", 0.1),
            "max_tokens": self.config.get("max_tokens", 4000),
        }
        
        # 如果配置了api_key和base_url，使用本地LLM
        if "api_key" in self.config:
            llm_kwargs["api_key"] = self.config["api_key"]
        if "base_url" in self.config:
            llm_kwargs["base_url"] = self.config["base_url"]
        
        self.llm = ChatOpenAI(**llm_kwargs)
        
        # 初始化工具
        self.tools = self._init_tools()
        
        # 初始化状态管理器
        self.state_manager = CodeReviewStateManager()
        
        # 创建智能体
        self.agent = self._create_agent()
        
        # 对话历史
        self.conversation_history: List[Dict[str, str]] = []
    
    def _init_tools(self) -> List[Any]:
        """初始化工具集"""
        return [
            StyleCheckerTool(llm=self.llm),
            QualityAssessorTool(llm=self.llm),
            SecurityScannerTool(llm=self.llm),
            PerformanceAnalyzerTool(llm=self.llm),
            ComplexityAnalyzerTool(llm=self.llm),
            RefactoringAdvisorTool(llm=self.llm)
        ]
    
    def _create_agent(self):
        """创建智能体"""
        # 使用新的 create_agent API
        agent = create_agent(
            model=self.llm,
            tools=self.tools,
            system_prompt=CODE_REVIEW_SYSTEM_PROMPT
        )
        return agent
    
    async def review_code(
        self,
        code_files: List[Dict[str, Any]],
        project_info: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        审查代码
        
        Args:
            code_files: 代码文件列表
            project_info: 项目信息
            
        Returns:
            审查结果
        """
        # 更新状态
        self.state_manager.set_code_files(code_files)
        if project_info:
            self.state_manager.set_project_info(project_info)
        self.state_manager.set_status("in_progress")
        
        # 添加到对话历史
        self.conversation_history.append({
            "role": "user",
            "content": f"审查 {len(code_files)} 个代码文件",
            "timestamp": datetime.now().isoformat()
        })
        
        try:
            all_issues = []
            file_reviews = []
            
            # 逐文件审查
            for i, code_file in enumerate(code_files):
                file_path = code_file.get("path", f"file_{i}")
                
                # 步骤1: 代码风格检查
                self.state_manager.update("current_file", file_path)
                self.state_manager.update("current_step", "style_check")
                style_result = await self._check_style(code_file)
                
                # 步骤2: 代码质量评估
                self.state_manager.update("current_step", "quality_assessment")
                quality_result = await self._assess_quality(code_file)
                
                # 步骤3: 安全扫描
                self.state_manager.update("current_step", "security_scan")
                security_result = await self._scan_security(code_file)
                
                # 步骤4: 性能分析
                self.state_manager.update("current_step", "performance_analysis")
                performance_result = await self._analyze_performance(code_file)
                
                # 步骤5: 复杂度分析
                self.state_manager.update("current_step", "complexity_analysis")
                complexity_result = await self._analyze_complexity(code_file)
                
                # 收集问题
                file_issues = []
                for result in [style_result, quality_result, security_result, performance_result, complexity_result]:
                    if "issues" in result:
                        for issue in result["issues"]:
                            issue["file_path"] = file_path
                            file_issues.append(issue)
                            all_issues.append(issue)
                            self.state_manager.add_issue(issue)
                
                # 计算文件评分
                scores = {
                    "style": style_result.get("overall_style_score", 80),
                    "quality": quality_result.get("overall_quality_score", 80),
                    "security": security_result.get("security_score", 80),
                    "performance": performance_result.get("performance_score", 80),
                    "complexity": complexity_result.get("complexity_score", 80)
                }
                file_score = sum(scores.values()) / len(scores)
                
                # 文件审查结果
                file_review = {
                    "file_path": file_path,
                    "language": code_file.get("language", "unknown"),
                    "scores": scores,
                    "overall_score": file_score,
                    "issues_count": len(file_issues),
                    "approved": file_score >= 80 and not any(i.get("severity") == "critical" for i in file_issues)
                }
                file_reviews.append(file_review)
                self.state_manager.add_file_review(file_review)
            
            # 步骤6: 生成重构建议
            self.state_manager.update("current_step", "generating_suggestions")
            refactoring_result = await self._generate_refactoring_suggestions(
                code_files, all_issues
            )
            
            for suggestion in refactoring_result.get("refactoring_suggestions", []):
                self.state_manager.add_refactoring_suggestion(suggestion)
            
            for practice in refactoring_result.get("best_practices", []):
                self.state_manager.add_best_practice(practice)
            
            # 计算总体评分
            overall_score = self._calculate_overall_score(file_reviews)
            self.state_manager.set_overall_score(overall_score)
            
            # 计算各维度评分
            self._calculate_dimension_scores(file_reviews)
            
            # 步骤7: 做出审查决策
            self.state_manager.update("current_step", "making_decision")
            decision = await self._make_decision()
            
            # 更新状态
            self.state_manager.set_approved(decision.get("decision") == "approved")
            self.state_manager.set_review_notes(decision.get("review_notes", ""))
            self.state_manager.set_status("completed")
            
            # 返回完整结果
            return {
                "status": "success",
                "approved": decision.get("decision") == "approved",
                "decision": decision.get("decision"),
                "overall_score": overall_score,
                "scores": {
                    "code_quality": self.state_manager.get("code_quality_score"),
                    "security": self.state_manager.get("security_score"),
                    "performance": self.state_manager.get("performance_score"),
                    "maintainability": self.state_manager.get("maintainability_score")
                },
                "issues_summary": {
                    "total": self.state_manager.get("total_issues"),
                    "critical": self.state_manager.get("critical_issues"),
                    "high": self.state_manager.get("high_issues"),
                    "medium": self.state_manager.get("medium_issues"),
                    "low": self.state_manager.get("low_issues")
                },
                "file_reviews": file_reviews,
                "issues": all_issues,
                "refactoring_suggestions": self.state_manager.get("refactoring_suggestions"),
                "best_practices": self.state_manager.get("best_practices"),
                "decision": decision,
                "state": self.state_manager.get_all()
            }
            
        except Exception as e:
            self.state_manager.add_error(str(e))
            self.state_manager.set_status("error")
            return {
                "status": "error",
                "error": str(e),
                "state": self.state_manager.get_all()
            }
    
    async def _check_style(self, code_file: Dict[str, Any]) -> Dict[str, Any]:
        """检查代码风格"""
        tool = StyleCheckerTool(llm=self.llm)
        return await tool._arun(code_file)
    
    async def _assess_quality(self, code_file: Dict[str, Any]) -> Dict[str, Any]:
        """评估代码质量"""
        tool = QualityAssessorTool(llm=self.llm)
        return await tool._arun(code_file)
    
    async def _scan_security(self, code_file: Dict[str, Any]) -> Dict[str, Any]:
        """扫描安全漏洞"""
        tool = SecurityScannerTool(llm=self.llm)
        return await tool._arun(code_file)
    
    async def _analyze_performance(self, code_file: Dict[str, Any]) -> Dict[str, Any]:
        """分析性能问题"""
        tool = PerformanceAnalyzerTool(llm=self.llm)
        return await tool._arun(code_file)
    
    async def _analyze_complexity(self, code_file: Dict[str, Any]) -> Dict[str, Any]:
        """分析复杂度"""
        tool = ComplexityAnalyzerTool(llm=self.llm)
        return await tool._arun(code_file)
    
    async def _generate_refactoring_suggestions(
        self,
        code_files: List[Dict[str, Any]],
        issues: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """生成重构建议"""
        tool = RefactoringAdvisorTool(llm=self.llm)
        
        # 为每个有问题的文件生成重构建议
        all_suggestions = []
        all_practices = []
        
        for code_file in code_files:
            file_issues = [i for i in issues if i.get("file_path") == code_file.get("path")]
            if file_issues:
                result = await tool._arun(code_file, file_issues)
                all_suggestions.extend(result.get("refactoring_suggestions", []))
                all_practices.extend(result.get("best_practices", []))
        
        return {
            "refactoring_suggestions": all_suggestions,
            "best_practices": all_practices
        }
    
    async def _make_decision(self) -> Dict[str, Any]:
        """做出审查决策"""
        prompt = ChatPromptTemplate.from_messages([
            ("system", "你是一位资深的代码审查专家。请根据审查结果做出决策。"),
            ("human", f"""请根据以下审查结果做出决策：

审查结果：
- 总体评分：{self.state_manager.get('overall_score')}
- 代码质量：{self.state_manager.get('code_quality_score')}
- 安全评分：{self.state_manager.get('security_score')}
- 性能评分：{self.state_manager.get('performance_score')}

问题统计：
- 严重问题：{self.state_manager.get('critical_issues')}
- 高优先级：{self.state_manager.get('high_issues')}
- 中等优先级：{self.state_manager.get('medium_issues')}
- 低优先级：{self.state_manager.get('low_issues')}

审查标准：
- 通过：无严重和高优先级问题，评分 >= 80
- 需修改：存在高优先级问题或评分 < 80
- 不通过：存在严重问题或评分 < 60

请以JSON格式输出决策。""")
        ])
        
        chain = prompt | self.llm
        result = chain.invoke({})
        
        try:
            parsed = json.loads(result.content)
        except json.JSONDecodeError:
            json_match = re.search(r'\{[\s\S]*\}', result.content)
            if json_match:
                parsed = json.loads(json_match.group())
            else:
                # 默认决策
                overall_score = self.state_manager.get("overall_score")
                critical_issues = self.state_manager.get("critical_issues")
                high_issues = self.state_manager.get("high_issues")
                
                if critical_issues > 0 or overall_score < 60:
                    decision = "rejected"
                elif high_issues > 0 or overall_score < 80:
                    decision = "needs_changes"
                else:
                    decision = "approved"
                
                parsed = {
                    "decision": decision,
                    "summary": f"审查完成，总体评分: {overall_score}",
                    "review_notes": f"发现 {self.state_manager.get('total_issues')} 个问题"
                }
        
        return parsed
    
    def _calculate_overall_score(self, file_reviews: List[Dict[str, Any]]) -> float:
        """计算总体评分"""
        if not file_reviews:
            return 0.0
        
        total_score = sum(r.get("overall_score", 0) for r in file_reviews)
        return total_score / len(file_reviews)
    
    def _calculate_dimension_scores(self, file_reviews: List[Dict[str, Any]]) -> None:
        """计算各维度评分"""
        if not file_reviews:
            return
        
        # 计算平均分
        style_scores = [r.get("scores", {}).get("style", 80) for r in file_reviews]
        quality_scores = [r.get("scores", {}).get("quality", 80) for r in file_reviews]
        security_scores = [r.get("scores", {}).get("security", 80) for r in file_reviews]
        performance_scores = [r.get("scores", {}).get("performance", 80) for r in file_reviews]
        complexity_scores = [r.get("scores", {}).get("complexity", 80) for r in file_reviews]
        
        self.state_manager.set_code_quality_score(sum(quality_scores) / len(quality_scores))
        self.state_manager.set_security_score(sum(security_scores) / len(security_scores))
        self.state_manager.set_performance_score(sum(performance_scores) / len(performance_scores))
        self.state_manager.set_maintainability_score(
            (sum(style_scores) + sum(complexity_scores)) / (2 * len(file_reviews))
        )
    
    def get_state(self) -> CodeReviewState:
        """获取当前状态"""
        return self.state_manager.get_all()
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """获取对话历史"""
        return self.conversation_history
    
    def get_issues(self) -> Dict[str, List[Dict[str, Any]]]:
        """获取问题列表"""
        return {
            "style": self.state_manager.get("style_issues"),
            "quality": self.state_manager.get("quality_issues"),
            "security": self.state_manager.get("security_issues"),
            "performance": self.state_manager.get("performance_issues"),
            "complexity": self.state_manager.get("complexity_issues")
        }
    
    def get_refactoring_suggestions(self) -> List[Dict[str, Any]]:
        """获取重构建议"""
        return self.state_manager.get("refactoring_suggestions")
    
    def reset(self) -> None:
        """重置智能体状态"""
        self.state_manager.reset()
        self.conversation_history = []


class CodeReviewAgentFactory:
    """代码审查智能体工厂"""
    
    @staticmethod
    def create(config: Optional[Dict[str, Any]] = None) -> CodeReviewAgent:
        """创建智能体实例"""
        return CodeReviewAgent(config)


# 导入json模块
import json
