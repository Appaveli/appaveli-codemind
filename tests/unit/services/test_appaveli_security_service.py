"""
Unit tests for AppaveliSecurityService.
"""
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language, SecurityIssue, SecuritySeverity
from appaveli_codemind.services.appaveli_security_service import AppaveliSecurityService


class TestAppaveliSecurityService:
    """Tests for AppaveliSecurityService class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        return client

    @pytest.fixture
    def language_detector(self):
        """Create a language detector."""
        return LanguageDetector()

    @pytest.fixture
    def security_service(self, mock_llm_client, language_detector):
        """Create a AppaveliSecurityService instance."""
        return AppaveliSecurityService(mock_llm_client, language_detector)

    def test_initialization(self, security_service, mock_llm_client, language_detector):
        """Test that AppaveliSecurityService initializes correctly."""
        assert security_service.llm_client == mock_llm_client
        assert security_service.language_detector == language_detector

    def test_scan_code_with_vulnerabilities(self, security_service, mock_llm_client):
        """Test scanning code that has vulnerabilities."""
        # Mock LLM response with security issues
        mock_llm_client.chat_completion.return_value = {
            "content": '''[
                {
                    "type": "sql_injection",
                    "severity": "high",
                    "line": 10,
                    "description": "SQL injection vulnerability",
                    "fix_suggestion": "Use parameterized queries"
                }
            ]'''
        }

        code = "SELECT * FROM users WHERE id = '" + "user_input" + "'"
        issues = security_service.scan_code(code, Language.JAVA)

        assert len(issues) == 1
        assert issues[0].type == "sql_injection"
        assert issues[0].severity == SecuritySeverity.HIGH
        assert issues[0].line == 10

    def test_scan_code_no_vulnerabilities(self, security_service, mock_llm_client):
        """Test scanning clean code."""
        mock_llm_client.chat_completion.return_value = {
            "content": "[]"
        }

        code = "def safe_function(): pass"
        issues = security_service.scan_code(code, Language.JAVASCRIPT)

        assert len(issues) == 0

    def test_scan_code_handles_llm_error(self, security_service, mock_llm_client):
        """Test that scan_code handles LLM errors gracefully."""
        mock_llm_client.chat_completion.side_effect = Exception("API error")

        code = "some code"
        issues = security_service.scan_code(code, Language.JAVA)

        # Should return empty list on error
        assert issues == []

    def test_scan_code_handles_invalid_json(self, security_service, mock_llm_client):
        """Test that scan_code handles invalid JSON responses."""
        mock_llm_client.chat_completion.return_value = {
            "content": "Invalid JSON response"
        }

        code = "some code"
        issues = security_service.scan_code(code, Language.JAVASCRIPT)

        assert issues == []

    def test_scan_code_multiple_vulnerabilities(self, security_service, mock_llm_client):
        """Test scanning code with multiple vulnerabilities."""
        mock_llm_client.chat_completion.return_value = {
            "content": '''[
                {
                    "type": "xss",
                    "severity": "medium",
                    "line": 5,
                    "description": "XSS vulnerability",
                    "fix_suggestion": "Sanitize input"
                },
                {
                    "type": "hardcoded_credentials",
                    "severity": "critical",
                    "line": 15,
                    "description": "Hardcoded password",
                    "fix_suggestion": "Use environment variables"
                }
            ]'''
        }

        code = "api_key = 'secret123'"
        issues = security_service.scan_code(code, Language.JAVASCRIPT)

        assert len(issues) == 2
        assert issues[0].type == "xss"
        assert issues[1].type == "hardcoded_credentials"
        assert issues[1].severity == SecuritySeverity.CRITICAL

    @patch('appaveli_codemind.services.appaveli_security_service.FileUtils')
    def test_scan_project(self, mock_file_utils, security_service, language_detector):
        """Test scanning an entire project."""
        # Mock file system
        mock_file_utils.find_files_by_extension.return_value = ["/project/test.java"]
        mock_file_utils.read_file.return_value = "public class Test {}"

        # Mock LLM response
        security_service.llm_client.chat_completion.return_value = {
            "content": '''[
                {
                    "type": "test_issue",
                    "severity": "low",
                    "line": 1,
                    "description": "Test issue",
                    "fix_suggestion": "Fix it"
                }
            ]'''
        }

        result = security_service.scan_project("/project")

        assert result.summary["total_code_issues"] >= 0
        assert result.recommendations is not None
        assert isinstance(result.recommendations, list)

    def test_generate_recommendations(self, security_service):
        """Test generating security recommendations."""
        issues = [
            SecurityIssue(
                type="sql_injection",
                severity=SecuritySeverity.HIGH,
                line=10,
                description="SQL injection",
                fix_suggestion="Use parameterized queries"
            )
        ]

        recommendations = security_service.generate_recommendations(issues)

        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        assert any("injection" in rec.lower() for rec in recommendations)

    def test_scan_code_with_column_number(self, security_service, mock_llm_client):
        """Test scanning code with column numbers in issues."""
        mock_llm_client.chat_completion.return_value = {
            "content": '''[
                {
                    "type": "buffer_overflow",
                    "severity": "critical",
                    "line": 20,
                    "column": 15,
                    "description": "Buffer overflow risk",
                    "fix_suggestion": "Use safe string functions"
                }
            ]'''
        }

        code = "strcpy(buffer, user_input);"
        issues = security_service.scan_code(code, Language.CPP)

        assert len(issues) == 1
        assert issues[0].column == 15
        assert issues[0].line == 20
