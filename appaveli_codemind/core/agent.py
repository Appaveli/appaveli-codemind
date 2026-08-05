"""
Main Appaveli CodeMind agent implementation
"""

import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

from appaveli_codemind.ai.llm_client import get_llm_client
from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import (
    AnalysisResult,
    BoilerplateType,
    CodeSuggestion,
    GenerationResult,
    Language,
    RefactorResult,
    RefactorType,
    SecurityIssue,
    SecurityScanResult,
    SecuritySeverity,
)
from appaveli_codemind.services.appaveli_analysis_service import AppaveliAnalysisService
from appaveli_codemind.services.appaveli_code_transform import AppaveliCodeTransform
from appaveli_codemind.services.appaveli_security_service import AppaveliSecurityService
from appaveli_codemind.utils.file_utils import FileUtils
from appaveli_codemind.utils.logging_config import setup_logging


class CodeMindAgent:
    """
    Main Appaveli CodeMind agent that orchestrates all functionality.

    This agent acts as a coordinator, delegating work to specialized services:
    - SecurityService: Security scanning
    - AnalysisService: Code analysis
    - RefactorService: Code refactoring
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        llm_provider: str = "openai",
        config: Optional[Dict[str, Any]] = None,
    ):
        """
        Initialize the CodeMind agent

        Args:
            api_key: API key for the selected LLM provider (or env var)
            llm_provider: 'openai' or 'anthropic'
            config: Optional configuration dictionary
        """
        setup_logging()
        self.logger = logging.getLogger(__name__)

        self.config = config or {}

        self.llm_client = get_llm_client(provider=llm_provider, api_key=api_key)
        self.logger.info(
            f"Using LLM client: {type(self.llm_client).__name__} (provider={llm_provider})"
        )

        self.language_detector = LanguageDetector()

        # Initialize Appaveli services
        self.security_service = AppaveliSecurityService(self.llm_client, self.language_detector)
        self.code_transform = AppaveliCodeTransform(self.llm_client, self.language_detector)
        self.analysis_service = AppaveliAnalysisService(
            self.llm_client, self.language_detector, self.security_service
        )

        self.logger.info("Appaveli CodeMind agent initialized successfully")

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Perform comprehensive analysis of a code file.

        Delegates to AnalysisService.

        Args:
            file_path: Path to the file to analyze

        Returns:
            AnalysisResult with comprehensive analysis
        """
        return self.analysis_service.analyze_file(file_path)

    def refactor_file(
        self, file_path: str, refactor_type: RefactorType, output_path: Optional[str] = None
    ) -> RefactorResult:
        """
        Refactor a code file.

        Delegates to AppaveliCodeTransform.

        Args:
            file_path: Path to the file to refactor
            refactor_type: Type of refactoring to perform
            output_path: Optional output path (defaults to overwriting original)

        Returns:
            RefactorResult with refactoring details
        """
        return self.code_transform.refactor_file(file_path, refactor_type, output_path)

    def generate_boilerplate(
        self, template_type: BoilerplateType, name: str, output_path: Optional[str] = None, **kwargs
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
            cost_estimate=self.llm_client.estimate_cost(len(generated_code.split())),
        )

        # Save generated code if output path provided
        if output_path and result.success:
            FileUtils.write_file(output_path, generated_code)
            self.logger.info(f"Generated code saved to: {output_path}")

        return result

    def generate_tests(
        self, file_path: str, test_type: str = "unit", output_path: Optional[str] = None
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
        Perform comprehensive security scan of entire project.

        Delegates to SecurityService.

        Args:
            project_path: Path to project directory

        Returns:
            SecurityScanResult with comprehensive security analysis
        """
        return self.security_service.scan_project(project_path)

    # Service delegation methods removed - now handled by dedicated services
    # - Security scanning: SecurityService
    # - Code analysis: AnalysisService
    # - Refactoring: RefactorService

    def _generate_boilerplate_with_ai(
        self, template_type: BoilerplateType, name: str, **kwargs
    ) -> str:
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
            # Add Laravel types here
            BoilerplateType.LARAVEL_CONTROLLER: f"""
            Create a Laravel controller in PHP named {name}.
            - Use the proper namespace and class structure
            - Include index, show, store, update, and destroy methods
            - Return JSON responses
            """,
            BoilerplateType.LARAVEL_MODEL: f"""
            Create a Laravel Eloquent model in PHP named {name}.
            - Include fillable fields: {kwargs.get('fields', 'name, email')}
            - Use appropriate namespace and PSR-4 structure
            """,
            BoilerplateType.LARAVEL_MIGRATION: f"""
            Create a Laravel migration in PHP to create a '{name.lower()}' table.
            - Use Schema builder
            - Include common fields like id, timestamps, and: {kwargs.get('fields', 'name, email')}
            """,
            BoilerplateType.LARAVEL_SEEDER: f"""
            Create a Laravel seeder class in PHP named {name}Seeder.
            - Use DB::table to insert sample data
            - Include use statements and namespace
            """,
            BoilerplateType.LARAVEL_REQUEST: f"""
            Create a Laravel FormRequest class in PHP named {name}Request.
            - Include validation rules
            - Use proper namespace and authorize() method
            """,
            BoilerplateType.LARAVEL_RESOURCE: f"""
            Create a Laravel API Resource in PHP named {name}Resource.
            - Implement the toArray method
            - Map fields from the model to API output
            """,
            BoilerplateType.LARAVEL_ROUTE: f"""
            Define Laravel API routes in PHP for the {name} controller.
            - Use Route::apiResource('{name.lower()}', {name}Controller::class);
            """,
            BoilerplateType.REACT_COMPONENT: f"""
            Create a React component named {name} with:
            - Functional component with hooks
            - TypeScript if applicable
            - Modern React patterns
            - PropTypes or TypeScript interfaces
            """,
        }

        prompt = template_prompts.get(
            template_type, f"Create a {template_type.value} template named {name}"
        )

        try:
            response = self.llm_client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": "You are an expert software developer. Generate clean, production-ready code.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            return response["content"]
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
            Language.CPP: "Google Test",
            Language.PHP: "PHPUnit",
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
            response = self.llm_client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": f"You are an expert in {language.value} testing and {framework}.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            return response["content"]
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
            BoilerplateType.LARAVEL_CONTROLLER: Language.PHP,
            BoilerplateType.LARAVEL_MODEL: Language.PHP,
            BoilerplateType.LARAVEL_MIGRATION: Language.PHP,
            BoilerplateType.LARAVEL_SEEDER: Language.PHP,
            BoilerplateType.LARAVEL_REQUEST: Language.PHP,
            BoilerplateType.LARAVEL_RESOURCE: Language.PHP,
            BoilerplateType.LARAVEL_ROUTE: Language.PHP,
        }

        return template_language_map.get(template_type, Language.JAVA)

