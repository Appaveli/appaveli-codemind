"""
Unit tests for AppaveliAnalysisService.
"""
import os
import pytest
from datetime import datetime
from unittest.mock import MagicMock, Mock, patch

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language, SecurityIssue, SecuritySeverity
from appaveli_codemind.services.appaveli_analysis_service import AppaveliAnalysisService
from appaveli_codemind.services.appaveli_security_service import AppaveliSecurityService


class TestAppaveliAnalysisService:
    """Tests for AppaveliAnalysisService class."""

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
    def mock_security_service(self):
        """Create a mock AppaveliSecurityService."""
        service = MagicMock(spec=AppaveliSecurityService)
        service.scan_code.return_value = []
        return service

    @pytest.fixture
    def analysis_service(self, mock_llm_client, language_detector, mock_security_service):
        """Create an AppaveliAnalysisService instance."""
        return AppaveliAnalysisService(mock_llm_client, language_detector, mock_security_service)

    def test_initialization(
        self, analysis_service, mock_llm_client, language_detector, mock_security_service
    ):
        """Test that AppaveliAnalysisService initializes correctly."""
        assert analysis_service.llm_client == mock_llm_client
        assert analysis_service.language_detector == language_detector
        assert analysis_service.security_service == mock_security_service

    @patch('appaveli_codemind.services.appaveli_analysis_service.FileUtils')
    def test_analyze_file_python(
        self, mock_file_utils, analysis_service, mock_llm_client, mock_security_service
    ):
        """Test analyzing a Python file."""
        # Mock file operations
        mock_file_utils.read_file.return_value = "def hello():\n    print('Hello')"

        # Mock LLM summary response
        mock_llm_client.chat_completion.return_value = {
            "content": "This is a simple Python function that prints Hello."
        }

        # Create a temporary file path
        with patch('os.path.exists', return_value=True):
            result = analysis_service.analyze_file("test.js")

        assert result.language == Language.JAVASCRIPT
        assert result.line_count == 2
        assert result.summary is not None
        assert result.file_path == "test.js"

    @patch('appaveli_codemind.services.appaveli_analysis_service.FileUtils')
    def test_analyze_file_with_security_issues(
        self, mock_file_utils, analysis_service, mock_llm_client, mock_security_service
    ):
        """Test analyzing a file with security issues."""
        mock_file_utils.read_file.return_value = "SELECT * FROM users WHERE id = '" + "input" + "'"

        # Mock security issues
        mock_security_service.scan_code.return_value = [
            SecurityIssue(
                type="sql_injection",
                severity=SecuritySeverity.HIGH,
                line=1,
                description="SQL injection vulnerability",
                fix_suggestion="Use parameterized queries"
            )
        ]

        mock_llm_client.chat_completion.return_value = {
            "content": "SQL query with potential vulnerability"
        }

        with patch('os.path.exists', return_value=True):
            result = analysis_service.analyze_file("test.java")

        assert len(result.security_issues) == 1
        assert result.security_issues[0].type == "sql_injection"

    def test_analyze_file_not_found(self, analysis_service):
        """Test analyzing a non-existent file."""
        with pytest.raises(FileNotFoundError):
            analysis_service.analyze_file("/nonexistent/file.py")

    @patch('appaveli_codemind.services.appaveli_analysis_service.FileUtils')
    def test_analyze_file_unsupported_type(
        self, mock_file_utils, analysis_service
    ):
        """Test analyzing an unsupported file type."""
        mock_file_utils.read_file.return_value = "some content"

        with patch('os.path.exists', return_value=True):
            with pytest.raises(ValueError, match="Unsupported file type"):
                analysis_service.analyze_file("file.unknown")

    def test_get_code_suggestions(self, analysis_service):
        """Test getting code suggestions."""
        code = "def test(): pass"
        suggestions = analysis_service.get_code_suggestions(code, Language.JAVASCRIPT)

        # Currently returns empty list (placeholder)
        assert isinstance(suggestions, list)

    def test_summarize_code_success(self, analysis_service, mock_llm_client):
        """Test successful code summarization."""
        mock_llm_client.chat_completion.return_value = {
            "content": "This code implements a user authentication system."
        }

        summary = analysis_service.summarize_code("def login():", Language.JAVASCRIPT)

        assert summary == "This code implements a user authentication system."
        assert "authentication" in summary.lower()

    def test_summarize_code_llm_error(self, analysis_service, mock_llm_client):
        """Test code summarization when LLM fails."""
        mock_llm_client.chat_completion.side_effect = Exception("API error")

        summary = analysis_service.summarize_code("code", Language.JAVA)

        assert summary == "Summary not available."

    @patch('appaveli_codemind.services.appaveli_analysis_service.FileUtils')
    def test_analyze_file_java(
        self, mock_file_utils, analysis_service, mock_llm_client, mock_security_service
    ):
        """Test analyzing a Java file."""
        java_code = '''
        public class HelloWorld {
            public static void main(String[] args) {
                System.out.println("Hello, World!");
            }
        }
        '''
        mock_file_utils.read_file.return_value = java_code
        mock_llm_client.chat_completion.return_value = {
            "content": "A simple Hello World program in Java."
        }

        with patch('os.path.exists', return_value=True):
            result = analysis_service.analyze_file("HelloWorld.java")

        assert result.language == Language.JAVA
        assert result.line_count > 0
        assert result.summary is not None

    @patch('appaveli_codemind.services.appaveli_analysis_service.FileUtils')
    def test_analyze_file_metadata(
        self, mock_file_utils, analysis_service, mock_llm_client, mock_security_service
    ):
        """Test that analysis result contains proper metadata."""
        mock_file_utils.read_file.return_value = "code"
        mock_llm_client.chat_completion.return_value = {"content": "summary"}

        with patch('os.path.exists', return_value=True):
            result = analysis_service.analyze_file("test.js")

        assert result.analysis_timestamp is not None
        assert isinstance(result.analysis_timestamp, datetime)
        assert result.file_path == "test.js"
