"""
Security scanning service.

Handles all security-related functionality including vulnerability detection
and security scanning for code files and projects.
"""
import logging
import os
from datetime import datetime
from typing import List

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language, SecurityIssue, SecurityScanResult, SecuritySeverity
from appaveli_codemind.utils.file_utils import FileUtils


class AppaveliSecurityService:
    """
    Service for security scanning and vulnerability detection.

    Responsibilities:
    - Scan individual files for security issues
    - Scan entire projects for vulnerabilities
    - Generate security recommendations
    """

    def __init__(self, llm_client, language_detector: LanguageDetector):
        """
        Initialize the security service.

        Args:
            llm_client: LLM client for AI-powered security analysis
            language_detector: Language detector for identifying file types
        """
        self.llm_client = llm_client
        self.language_detector = language_detector
        self.logger = logging.getLogger(__name__)

    def scan_code(self, code: str, language: Language) -> List[SecurityIssue]:
        """
        Scan code for security vulnerabilities using AI.

        Args:
            code: Source code to analyze
            language: Programming language of the code

        Returns:
            List of security issues found
        """
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
            response = self.llm_client.chat_completion(
                [
                    {
                        "role": "system",
                        "content": "You are a security expert. Return only valid JSON.",
                    },
                    {"role": "user", "content": prompt},
                ]
            )

            import json
            import re

            json_match = re.search(r"\[.*\]", response["content"], re.DOTALL)
            if json_match:
                issues_data = json.loads(json_match.group())
                return [
                    SecurityIssue(
                        type=issue.get("type", "unknown"),
                        severity=SecuritySeverity(issue.get("severity", "medium")),
                        line=issue.get("line", 1),
                        column=issue.get("column"),
                        description=issue.get("description", ""),
                        fix_suggestion=issue.get("fix_suggestion", ""),
                    )
                    for issue in issues_data
                ]
        except Exception as e:
            self.logger.warning(f"Security scan failed: {e}")

        return []

    def scan_project(self, project_path: str) -> SecurityScanResult:
        """
        Perform comprehensive security scan of entire project.

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
                        issues = self.scan_code(content, language)
                        for issue in issues:
                            issue.file_path = file_path
                        code_issues.extend(issues)
                except Exception as e:
                    self.logger.warning(f"Could not scan {file_path}: {e}")

        summary = {
            "total_code_issues": len(code_issues),
            "high_severity_issues": len(
                [
                    i
                    for i in code_issues
                    if i.severity in [SecuritySeverity.HIGH, SecuritySeverity.CRITICAL]
                ]
            ),
            "total_dependency_vulnerabilities": 0,  # TODO: Implement dependency scanning
            "critical_vulnerabilities": 0,
        }

        return SecurityScanResult(
            file_path=project_path,
            language=Language.JAVA,  # Default, not really applicable for project scan
            code_issues=code_issues,
            dependency_vulnerabilities=[],  # TODO: Implement later
            scan_timestamp=datetime.now(),
            summary=summary,
            recommendations=self.generate_recommendations(code_issues),
        )

    def generate_recommendations(self, issues: List[SecurityIssue]) -> List[str]:
        """
        Generate security recommendations based on found issues.

        Args:
            issues: List of security issues

        Returns:
            List of security recommendations
        """
        recommendations = [
            "Implement input validation for all user inputs",
            "Use parameterized queries to prevent SQL injection",
            "Enable security headers in your web application",
            "Regularly update dependencies to latest secure versions",
            "Implement proper authentication and authorization",
            "Use HTTPS for all communications",
            "Implement proper error handling without exposing sensitive information",
        ]

        return recommendations
