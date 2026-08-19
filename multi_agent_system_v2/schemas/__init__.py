"""
Schema层：所有数据类型定义
"""

from .requirements import (
    RequirementItem,
    UserStory,
    AcceptanceCriterion,
    PriorityMatrix,
    RequirementsOutput,
)
from .technical import (
    TechStack,
    APIEndpoint,
    APIDesign,
    DatabaseTable,
    DatabaseDesign,
    SecurityDesign,
    ArchitectureDesign,
    CostEstimation,
    TechnicalOutput,
)
from .code import CodeFile, MVPCodeOutput, CodeReviewIssue, CodeReviewOutput
from .testing import TestCase, TestCoverage, Bug, TestingOutput
from .acceptance import AcceptanceResult, AcceptanceOutput
from .deployment import (
    DeploymentEnvironment,
    DeploymentPlan,
    DockerConfig,
    KubernetesConfig,
    CICDConfig,
    MonitoringConfig,
    DeploymentOutput,
)
from .pipeline import StageResult, PipelineResult
from .spec import ProjectSpec, EndpointSpec, RuleSpec

__all__ = [
    # Requirements
    "RequirementItem",
    "UserStory",
    "AcceptanceCriterion",
    "PriorityMatrix",
    "RequirementsOutput",
    # Technical
    "TechStack",
    "APIEndpoint",
    "APIDesign",
    "DatabaseTable",
    "DatabaseDesign",
    "SecurityDesign",
    "ArchitectureDesign",
    "CostEstimation",
    "TechnicalOutput",
    # Code
    "CodeFile",
    "MVPCodeOutput",
    "CodeReviewIssue",
    "CodeReviewOutput",
    # Testing
    "TestCase",
    "TestCoverage",
    "Bug",
    "TestingOutput",
    # Acceptance
    "AcceptanceResult",
    "AcceptanceOutput",
    # Deployment
    "DeploymentEnvironment",
    "DeploymentPlan",
    "DockerConfig",
    "KubernetesConfig",
    "CICDConfig",
    "MonitoringConfig",
    "DeploymentOutput",
    # Pipeline
    "StageResult",
    "PipelineResult",
    # Spec
    "ProjectSpec",
    "EndpointSpec",
    "RuleSpec",
]
