"""
Main Appaveli CodeMind agent implementation
"""

import os
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from appaveli_codemind.core.models import (
    Language, BoilerplateType, SecurityIssue, AnalysisResult,
    RefactorResult, GenerationResult, SecurityScanResult, RefactorType,
    CodeSuggestion, SecuritySeverity
)
from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.ai.llm_client import OpenAIClient
from appaveli_codemind.utils.file_utils import FileUtils
from appaveli_codemind.utils.logging_config import setup_logging


class CodeMindAgent:
    """
    Main Appaveli CodeMind agent that orchestrates all functionality
    """
    
    def __init__(self, api_key: Optional[str] = None, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the CodeMind agent
        
        Args:
            api_key: OpenAI API key (if not provided, will look for env var)
            config: Optional configuration dictionary
        """
        # Setup logging
        setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # Initialize configuration
        self.config = config or {}
        
        # Initialize OpenAI client
        self.openai_client = OpenAIClient(api_key)
        
        # Initialize components
        self.language_detector = LanguageDetector()
        
        self.logger.info("Appaveli CodeMind agent initialized successfully")
    
    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Perform comprehensive analysis of a code file
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            AnalysisResult with comprehensive analysis
        """
        self.logger.info(f"Analyzing file: {file_path}")
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Read file content
        content = FileUtils.read_file(file_path)
        
        # Detect language
        language = self.language_detector.detect(file_path)
        if not language:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Perform basic analysis
        security_issues = self._scan_code_security(content, language)
        code_suggestions = self._get_code_suggestions(content, language)
        
        # Calculate metrics
        line_count = len(content.split('\n'))
        
        return AnalysisResult(
            file_path=file_path,
            language=language,
            line_count=line_count,
            security_issues=security_issues,
            code_suggestions=code_suggestions,
            complexity_score=None,
            maintainability_score=None,
            test_coverage_estimate=None,
            analysis_timestamp=datetime.now()
        )
    
    def refactor_file(
        self, 
        file_path: str, 
        refactor_type: RefactorType, 
        output_path: Optional[str] = None
    ) -> RefactorResult:
        """
        Refactor a code file
        
        Args:
            file_path: Path to the file to refactor
            refactor_type: Type of refactoring to perform
            output_path: Optional output path (defaults to overwriting original)
            
        Returns:
            RefactorResult with refactoring details
        """
        self.logger.info(f"Refactoring file: {file_path} with type: {refactor_type.value}")
        
        # Read original file
        original_code = FileUtils.read_file(file_path)
        
        # Detect language
        language = self.language_detector.detect(file_path)
        if not language:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        # Perform refactoring using AI
        refactored_code = self._refactor_code_with_ai(original_code, language, refactor_type)
        
        # Create result object
        result = RefactorResult(
            success=True,
            original_code=original_code,
            refactored_code=refactored_code,
            language=language,
            refactor_type=refactor_type,
            suggestions=[],
            changes_made=["Code refactored using AI analysis"],
            tokens_used=len(original_code.split()) + len(refactored_code.split()),
            cost_estimate=self.openai_client.estimate_cost(len(original_code.split()) + len(refactored_code.split()))
        )
        
        # Save refactored code if output path provided
        if output_path:
            FileUtils.write_file(output_path, refactored_code)
            self.logger.info(f"Refactored code saved to: {output_path}")
        
        return result
    
    def generate_boilerplate(
        self,
        template_type: BoilerplateType,
        name: str,
        output_path: Optional[str] = None,
        **kwargs
    ) -> GenerationResult:
        """
        Generate boilerplate code
        
        Args:
            template_type: Type of boilerplate to generate
            name: Name for the generated component
            output_path: Optional output file path
            **kwargs: Additional template parameters
            
        Returns:
            GenerationResult with generated code
        """
        self.logger.info(f"Generating {template_type.value} boilerplate: {name}")
        
        # Generate code using AI
        generated_code = self._generate_boilerplate_with_ai(template_type, name, **kwargs)
        
        # Determine language from template type
        language = self._get_language_from_template(template_type)
        
        result = GenerationResult(
            success=True,
            generated_code=generated_code,
            template_type=template_type,
            language=language,
            name=name,
            metadata=kwargs,
            tokens_used=len(generated_code.split()),
            cost_estimate=self.openai_client.estimate_cost(len(generated_code.split()))
        )
        
        # Save generated code if output path provided
        if output_path and result.success:
            FileUtils.write_file(output_path, generated_code)
            self.logger.info(f"Generated code saved to: {output_path}")
        
        return result
    
    def generate_tests(
        self,
        file_path: str,
        test_type: str = "unit",
        output_path: Optional[str] = None
    ) -> str:
        """
        Generate tests for a code file
        
        Args:
            file_path: Path to the file to generate tests for
            test_type: Type of tests to generate (unit, integration)
            output_path: Optional output file path
            
        Returns:
            Generated test code as string
        """
        self.logger.info(f"Generating {test_type} tests for: {file_path}")
        
        source_code = FileUtils.read_file(file_path)
        
        language = self.language_detector.detect(file_path)
        if not language:
            raise ValueError(f"Unsupported file type: {file_path}")
        
        test_code = self._generate_tests_with_ai(source_code, language, test_type)
        
        if output_path:
            FileUtils.write_file(output_path, test_code)
            self.logger.info(f"Generated tests saved to: {output_path}")
        
        return test_code
    
    def scan_project_security(self, project_path: str) -> SecurityScanResult:
        """
        Perform comprehensive security scan of entire project
        
        Args:
            project_path: Path to project directory
            
        Returns:
            SecurityScanResult with comprehensive security analysis
        """
        self.logger.info(f"Scanning project security: {project_path}")
        
        # Scan all supported files in the project
        code_issues = []
        
        # Find all supported code files
        for ext in self.language_detector.get_supported_extensions():
            files = FileUtils.find_files_by_extension(project_path, [ext])
            for file_path in files:
                try:
                    content = FileUtils.read_file(file_path)
                    language = self.language_detector.detect(file_path)
                    if language:
                        issues = self._scan_code_security(content, language)
                        for issue in issues:
                            issue.file_path = file_path
                        code_issues.extend(issues)
                except Exception as e:
                    self.logger.warning(f"Could not scan {file_path}: {e}")
        
        summary = {
            "total_code_issues": len(code_issues),
            "high_severity_issues": len([i for i in code_issues if i.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]]),
            "total_dependency_vulnerabilities": 0,  # TODO: Implement dependency scanning
            "critical_vulnerabilities": 0
        }
        
        return SecurityScanResult(
            file_path=project_path,
            language=Language.JAVA,  # Default, not really applicable for project scan
            code_issues=code_issues,
            dependency_vulnerabilities=[],  # TODO: Implement later
            scan_timestamp=datetime.now(),
            summary=summary,
            recommendations=self._generate_security_recommendations(code_issues)
        )
    
    def _scan_code_security(self, code: str, language: Language) -> List[SecurityIssue]:
        """Scan code for security vulnerabilities using AI"""
        prompt = f"""
        Analyze this {language.value} code for security vulnerabilities:
        
        {code[:2000]}  # Truncate for cost efficiency
        
        Look for common issues like:
        - SQL injection vulnerabilities
        - XSS vulnerabilities  
        - Authentication/authorization issues
        - Input validation problems
        - Hardcoded credentials
        
        Return a JSON array of issues with format:
        [{{"type": "sql_injection", "severity": "high", "line": 15, "description": "...", "fix_suggestion": "..."}}]
        """
        
        try:
            response = self.openai_client.chat_completion([
                {"role": "system", "content": "You are a security expert. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ])
            
            import json
            import re
            
            json_match = re.search(r'\[.*\]', response['content'], re.DOTALL)
            if json_match:
                issues_data = json.loads(json_match.group())
                return [
                    SecurityIssue(
                        type=issue.get('type', 'unknown'),
                        severity=SecuritySeverity(issue.get('severity', 'medium')),
                        line=issue.get('line', 1),
                        column=issue.get('column'),
                        description=issue.get('description', ''),
                        fix_suggestion=issue.get('fix_suggestion', '')
                    )
                    for issue in issues_data
                ]
        except Exception as e:
            self.logger.warning(f"Security scan failed: {e}")
        
        return []
    
    def _get_code_suggestions(self, code: str, language: Language) -> List[CodeSuggestion]:
        """Get code improvement suggestions"""
        return []  # Placeholder
    
    def _refactor_code_with_ai(self, code: str, language: Language, refactor_type: RefactorType) -> str:
        """Refactor code using AI"""
        prompt = f"""
        Refactor this {language.value} code using {refactor_type.value.replace('_', ' ')} techniques:
        
        {code}
        
        Focus on:
        - Code readability and maintainability
        - Best practices for {language.value}
        - Performance improvements
        - Proper naming conventions
        
        Return only the refactored code without explanations.
        """
        
        try:
            response = self.openai_client.chat_completion([
                {"role": "system", "content": f"You are an expert {language.value} developer. Return only clean, refactored code."},
                {"role": "user", "content": prompt}
            ])
            
            return response['content']
        except Exception as e:
            self.logger.error(f"Refactoring failed: {e}")
            return code  # Return original code if refactoring fails
    
    def _generate_boilerplate_with_ai(self, template_type: BoilerplateType, name: str, **kwargs) -> str:
        """Generate boilerplate code using AI"""
        
        # Map template types to prompts
        template_prompts = {
            BoilerplateType.POJO: f"""
            Create a Java POJO class named {name} with:
            - Private fields: {kwargs.get('fields', 'id:Long, name:String')}
            - Getters and setters
            - Constructor with parameters
            - toString(), equals(), hashCode() methods
            - Package: {kwargs.get('package', 'com.appaveli.model')}
            """,
            BoilerplateType.SPRING_CONTROLLER: f"""
            Create a Spring Boot REST controller named {name} with:
            - @RestController annotation
            - CRUD endpoints (GET, POST, PUT, DELETE)
            - Proper HTTP status codes
            - Package: {kwargs.get('package', 'com.appaveli.controller')}
            """,
            BoilerplateType.SWIFTUI_VIEW: f"""
            Create a SwiftUI view named {name} with:
            - Proper SwiftUI structure
            - State management using @State
            - Modern SwiftUI patterns
            - Preview provider
            """,
            BoilerplateType.FLUTTER_WIDGET: f"""
            Create a Flutter widget named {name} with:
            - StatefulWidget structure
            - Build method implementation
            - Material Design components
            """,
            BoilerplateType.COMPOSE_SCREEN: f"""
            Create a Jetpack Compose screen named {name} with:
            - Composable function
            - State management with remember
            - Material Design 3 components
            - Navigation handling
            """,
            BoilerplateType.REACT_COMPONENT: f"""
            Create a React component named {name} with:
            - Functional component with hooks
            - TypeScript if applicable
            - Modern React patterns
            - PropTypes or TypeScript interfaces
            """
        }
        
        prompt = template_prompts.get(template_type, f"Create a {template_type.value} template named {name}")
        
        try:
            response = self.openai_client.chat_completion([
                {"role": "system", "content": "You are an expert software developer. Generate clean, production-ready code."},
                {"role": "user", "content": prompt}
            ])
            
            return response['content']
        except Exception as e:
            self.logger.error(f"Code generation failed: {e}")
            return f"// Error generating {template_type.value}: {e}"
    
    def _generate_tests_with_ai(self, source_code: str, language: Language, test_type: str) -> str:
        """Generate tests using AI"""
        
        test_frameworks = {
            Language.JAVA: "JUnit 5 with Mockito",
            Language.KOTLIN: "JUnit 5 with Mockito",
            Language.SWIFT: "XCTest",
            Language.DART: "Flutter test framework",
            Language.JAVASCRIPT: "Jest",
            Language.CPP: "Google Test"
        }
        
        framework = test_frameworks.get(language, "appropriate testing framework")
        
        prompt = f"""
        Generate {test_type} tests for this {language.value} code using {framework}:
        
        {source_code}
        
        Include:
        - Test all public methods
        - Edge cases and error scenarios
        - Proper setup and teardown
        - Mock dependencies where appropriate
        - Comprehensive assertions
        
        Return complete, runnable test code.
        """
        
        try:
            response = self.openai_client.chat_completion([
                {"role": "system", "content": f"You are an expert in {language.value} testing and {framework}."},
                {"role": "user", "content": prompt}
            ])
            
            return response['content']
        except Exception as e:
            self.logger.error(f"Test generation failed: {e}")
            return f"// Error generating tests: {e}"
    
    def _get_language_from_template(self, template_type: BoilerplateType) -> Language:
        """Get language from template type"""
        template_language_map = {
            BoilerplateType.POJO: Language.JAVA,
            BoilerplateType.REST_API_JERSEY: Language.JAVA,
            BoilerplateType.JSP_PAGE: Language.JAVA,
            BoilerplateType.SERVLET: Language.JAVA,
            BoilerplateType.SPRING_CONTROLLER: Language.JAVA,
            BoilerplateType.SPRING_SERVICE: Language.JAVA,
            BoilerplateType.SWIFTUI_VIEW: Language.SWIFT,
            BoilerplateType.SWIFTUI_VIEWMODEL: Language.SWIFT,
            BoilerplateType.IOS_MODEL: Language.SWIFT,
            BoilerplateType.COMPOSE_SCREEN: Language.KOTLIN,
            BoilerplateType.COMPOSE_COMPONENT: Language.KOTLIN,
            BoilerplateType.ANDROID_VIEWMODEL: Language.KOTLIN,
            BoilerplateType.FLUTTER_WIDGET: Language.DART,
            BoilerplateType.FLUTTER_SCREEN: Language.DART,
            BoilerplateType.FLUTTER_SERVICE: Language.DART,
            BoilerplateType.REACT_COMPONENT: Language.JAVASCRIPT,
            BoilerplateType.NODE_SERVICE: Language.JAVASCRIPT,
        }
        
        return template_language_map.get(template_type, Language.JAVA)
    
    def _generate_security_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """Generate security recommendations based on found issues"""
        recommendations = [
            "Implement input validation for all user inputs",
            "Use parameterized queries to prevent SQL injection",
            "Enable security headers in your web application",
            "Regularly update dependencies to latest secure versions",
            "Implement proper authentication and authorization",
            "Use HTTPS for all communications",
            "Implement proper error handling without exposing sensitive information"
        ]
        
        return recommendations
