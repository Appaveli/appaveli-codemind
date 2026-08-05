"""
Code analysis service.

Handles code analysis, summaries, and improvement suggestions.
"""
import logging
import os
from datetime import datetime
from typing import List

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import AnalysisResult, CodeSuggestion, Language, SecurityIssue
from appaveli_codemind.services.appaveli_security_service import AppaveliSecurityService
from appaveli_codemind.utils.file_utils import FileUtils


class AppaveliAnalysisService:
    """
    Service for code analysis and improvement suggestions.

    Responsibilities:
    - Analyze code files
    - Generate code summaries
    - Provide improvement suggestions
    """

    def __init__(
        self,
        llm_client,
        language_detector: LanguageDetector,
        security_service: AppaveliSecurityService,
    ):
        """
        Initialize the analysis service.

        Args:
            llm_client: LLM client for AI-powered analysis
            language_detector: Language detector for identifying file types
            security_service: Security service for security analysis
        """
        self.llm_client = llm_client
        self.language_detector = language_detector
        self.security_service = security_service
        self.logger = logging.getLogger(__name__)

    def analyze_file(self, file_path: str) -> AnalysisResult:
        """
        Perform comprehensive analysis of a code file.

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
        security_issues = self.security_service.scan_code(content, language)
        code_suggestions = self.get_code_suggestions(content, language)

        # Generate high-level summary
        summary = self.summarize_code(content, language)

        # Calculate metrics
        line_count = len(content.split("\n"))

        return AnalysisResult(
            file_path=file_path,
            language=language,
            line_count=line_count,
            security_issues=security_issues,
            code_suggestions=code_suggestions,
            complexity_score=None,
            maintainability_score=None,
            test_coverage_estimate=None,
            analysis_timestamp=datetime.now(),
            summary=summary,
        )

    def get_code_suggestions(self, code: str, language: Language) -> List[CodeSuggestion]:
        """
        Get code improvement suggestions.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            List of code improvement suggestions
        """
        # Placeholder - can be enhanced with AI-powered suggestions
        return []

    def summarize_code(self, code: str, language: Language) -> str:
        """
        Generate a high-level summary of code using AI.

        Args:
            code: Source code to summarize
            language: Programming language

        Returns:
            Summary of the code
        """
        prompt = f"""
        Summarize the following {language.value} code.

        - Identify the purpose of the file
        - Highlight major classes or functions
        - Mention any key logic or responsibilities

        Return a clear, professional summary under 150 words.

        Code:
        {code[:3000]}  # Truncate for token cost efficiency
        """

        try:
            response = self.llm_client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": "You are a senior software engineer who writes clear and concise code summaries.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )
            return response["content"].strip()
        except Exception as e:
            self.logger.warning(f"Code summarization failed: {e}")
            return "Summary not available."
