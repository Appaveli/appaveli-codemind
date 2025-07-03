"""
Core data models and enums for Appaveli CodeMind
"""

from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime


class Language(Enum):
    """Supported programming languages"""
    JAVA = "java"
    KOTLIN = "kotlin"
    SWIFT = "swift"
    CPP = "cpp"
    DART = "dart"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class BoilerplateType(Enum):
    """Types of boilerplate code that can be generated"""
    # Java/Kotlin
    POJO = "pojo"
    REST_API_JERSEY = "rest_api_jersey"
    JSP_PAGE = "jsp_page"
    SERVLET = "servlet"
    JUNIT_TEST = "junit_test"
    SPRING_CONTROLLER = "spring_controller"
    SPRING_SERVICE = "spring_service"
    
    # Swift/iOS
    SWIFTUI_VIEW = "swiftui_view"
    SWIFTUI_VIEWMODEL = "swiftui_viewmodel"
    XCTEST_UNIT = "xctest_unit"
    IOS_MODEL = "ios_model"
    
    # Android/Kotlin
    COMPOSE_SCREEN = "compose_screen"
    COMPOSE_COMPONENT = "compose_component"
    ANDROID_VIEWMODEL = "android_viewmodel"
    ANDROID_REPOSITORY = "android_repository"
    
    # Flutter/Dart
    FLUTTER_WIDGET = "flutter_widget"
    FLUTTER_SCREEN = "flutter_screen"
    FLUTTER_SERVICE = "flutter_service"
    FLUTTER_MODEL = "flutter_model"
    
    # JavaScript/TypeScript
    REACT_COMPONENT = "react_component"
    NODE_SERVICE = "node_service"
    EXPRESS_ROUTE = "express_route"
    
    # Cross-platform
    API_CLIENT = "api_client"
    DATA_MODEL = "data_model"


class SecuritySeverity(Enum):
    """Security issue severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class RefactorType(Enum):
    """Types of code refactoring"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    RENAME_VARIABLE = "rename_variable"
    SIMPLIFY_CONDITIONAL = "simplify_conditional"
    REMOVE_DUPLICATE = "remove_duplicate"
    OPTIMIZE_IMPORTS = "optimize_imports"
    IMPROVE_NAMING = "improve_naming"
    APPLY_DESIGN_PATTERN = "apply_design_pattern"
    PERFORMANCE_OPTIMIZATION = "performance_optimization"
    GENERAL_CLEANUP = "general_cleanup"


@dataclass
class SecurityIssue:
    """Represents a security vulnerability found in code"""
    type: str
    severity: SecuritySeverity
    line: int
    column: Optional[int]
    description: str
    fix_suggestion: str
    file_path: Optional[str] = None
    rule_id: Optional[str] = None
    cwe_id: Optional[str] = None


@dataclass
class DependencyVulnerability:
    """Represents a vulnerability in project dependencies"""
    package: str
    current_version: str
    vulnerable_version: str
    severity: SecuritySeverity
    cve_id: str
    fix_version: str
    description: str
    advisory_url: Optional[str] = None


@dataclass
class CodeSuggestion:
    """Represents a code improvement suggestion"""
    type: str
    description: str
    line: Optional[int]
    original_code: Optional[str]
    suggested_code: Optional[str]
    confidence: float  # 0.0 to 1.0


@dataclass
class RefactorResult:
    """Result of a code refactoring operation"""
    success: bool
    original_code: str
    refactored_code: str
    language: Language
    refactor_type: RefactorType
    suggestions: List[CodeSuggestion]
    changes_made: List[str]
    tokens_used: int
    cost_estimate: float
    error_message: Optional[str] = None


@dataclass
class GenerationResult:
    """Result of a code generation operation"""
    success: bool
    generated_code: str
    template_type: BoilerplateType
    language: Language
    name: str
    metadata: Dict[str, Any]
    tokens_used: int
    cost_estimate: float
    error_message: Optional[str] = None


@dataclass
class SecurityScanResult:
    """Result of a security scan operation"""
    file_path: str
    language: Language
    code_issues: List[SecurityIssue]
    dependency_vulnerabilities: List[DependencyVulnerability]
    scan_timestamp: datetime
    summary: Dict[str, int]
    recommendations: List[str]


@dataclass
class AnalysisResult:
    """Comprehensive code analysis result"""
    file_path: str
    language: Language
    line_count: int
    security_issues: List[SecurityIssue]
    code_suggestions: List[CodeSuggestion]
    complexity_score: Optional[float]
    maintainability_score: Optional[float]
    test_coverage_estimate: Optional[float]
    analysis_timestamp: datetime