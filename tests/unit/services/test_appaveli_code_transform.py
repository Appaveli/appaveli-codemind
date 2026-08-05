"""
Unit tests for AppaveliCodeTransform.
"""
import pytest
from unittest.mock import MagicMock, Mock, patch

from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language, RefactorType
from appaveli_codemind.services.appaveli_code_transform import AppaveliCodeTransform


class TestAppaveliCodeTransform:
    """Tests for AppaveliCodeTransform class."""

    @pytest.fixture
    def mock_llm_client(self):
        """Create a mock LLM client."""
        client = MagicMock()
        client.estimate_cost.return_value = 0.05
        return client

    @pytest.fixture
    def language_detector(self):
        """Create a language detector."""
        return LanguageDetector()

    @pytest.fixture
    def refactor_service(self, mock_llm_client, language_detector):
        """Create a AppaveliCodeTransform instance."""
        return AppaveliCodeTransform(mock_llm_client, language_detector)

    def test_initialization(self, refactor_service, mock_llm_client, language_detector):
        """Test that AppaveliCodeTransform initializes correctly."""
        assert refactor_service.llm_client == mock_llm_client
        assert refactor_service.language_detector == language_detector

    def test_refactor_code_success(self, refactor_service, mock_llm_client):
        """Test successful code refactoring."""
        original_code = "def test():\n    x=1\n    return x"
        refactored_code = "def test():\n    x = 1\n    return x"

        mock_llm_client.chat_completion.return_value = {
            "content": refactored_code
        }

        result = refactor_service.refactor_code(
            original_code, Language.JAVASCRIPT, RefactorType.GENERAL_CLEANUP
        )

        assert result == refactored_code
        assert "x = 1" in result

    def test_refactor_code_llm_error(self, refactor_service, mock_llm_client):
        """Test refactoring when LLM fails."""
        original_code = "def test(): pass"
        mock_llm_client.chat_completion.side_effect = Exception("API error")

        result = refactor_service.refactor_code(
            original_code, Language.JAVASCRIPT, RefactorType.GENERAL_CLEANUP
        )

        # Should return original code on error
        assert result == original_code

    @patch('appaveli_codemind.services.appaveli_code_transform.FileUtils')
    def test_refactor_file_python(
        self, mock_file_utils, refactor_service, mock_llm_client
    ):
        """Test refactoring a JavaScript file."""
        original = "function test() { }"
        refactored = "const test = () => { };"

        mock_file_utils.read_file.return_value = original
        mock_llm_client.chat_completion.return_value = {"content": refactored}

        # Mock language detector to return JAVASCRIPT
        with patch.object(refactor_service.language_detector, 'detect', return_value=Language.JAVASCRIPT):
            result = refactor_service.refactor_file("test.js", RefactorType.GENERAL_CLEANUP)

        assert result.success is True
        assert result.original_code == original
        assert result.refactored_code == refactored
        assert result.language == Language.JAVASCRIPT
        assert result.refactor_type == RefactorType.GENERAL_CLEANUP

    @patch('appaveli_codemind.services.appaveli_code_transform.FileUtils')
    def test_refactor_file_with_output_path(
        self, mock_file_utils, refactor_service, mock_llm_client
    ):
        """Test refactoring with output file."""
        original = "code"
        refactored = "refactored code"

        mock_file_utils.read_file.return_value = original
        mock_llm_client.chat_completion.return_value = {"content": refactored}

        with patch.object(refactor_service.language_detector, 'detect', return_value=Language.JAVA):
            result = refactor_service.refactor_file(
                "test.java", RefactorType.GENERAL_CLEANUP, output_path="output.java"
            )

        # Verify file was written
        mock_file_utils.write_file.assert_called_once_with("output.java", refactored)
        assert result.success is True

    @patch('appaveli_codemind.services.appaveli_code_transform.FileUtils')
    def test_refactor_file_unsupported_type(
        self, mock_file_utils, refactor_service
    ):
        """Test refactoring unsupported file type."""
        mock_file_utils.read_file.return_value = "content"

        with pytest.raises(ValueError, match="Unsupported file type"):
            refactor_service.refactor_file("file.unknown", RefactorType.GENERAL_CLEANUP)

    def test_refactor_code_different_types(self, refactor_service, mock_llm_client):
        """Test different refactor types."""
        code = "function test() { var x = 1; }"
        refactored = "function test() { const x = 1; }"

        mock_llm_client.chat_completion.return_value = {"content": refactored}

        # Test GENERAL_CLEANUP
        result = refactor_service.refactor_code(code, Language.JAVASCRIPT, RefactorType.GENERAL_CLEANUP)
        assert "const" in result

        # Test PERFORMANCE_OPTIMIZATION
        result = refactor_service.refactor_code(code, Language.JAVASCRIPT, RefactorType.PERFORMANCE_OPTIMIZATION)
        assert isinstance(result, str)

    @patch('appaveli_codemind.services.appaveli_code_transform.FileUtils')
    def test_refactor_file_java(
        self, mock_file_utils, refactor_service, mock_llm_client
    ):
        """Test refactoring a Java file."""
        original_java = "public class Test { int x; }"
        refactored_java = "public class Test { private int x; }"

        mock_file_utils.read_file.return_value = original_java
        mock_llm_client.chat_completion.return_value = {"content": refactored_java}

        with patch.object(refactor_service.language_detector, 'detect', return_value=Language.JAVA):
            result = refactor_service.refactor_file("Test.java", RefactorType.GENERAL_CLEANUP)

        assert result.language == Language.JAVA
        assert "private" in result.refactored_code

    @patch('appaveli_codemind.services.appaveli_code_transform.FileUtils')
    def test_refactor_file_cost_estimation(
        self, mock_file_utils, refactor_service, mock_llm_client
    ):
        """Test that cost estimation is included in result."""
        mock_file_utils.read_file.return_value = "code"
        mock_llm_client.chat_completion.return_value = {"content": "refactored"}
        mock_llm_client.estimate_cost.return_value = 0.03

        with patch.object(refactor_service.language_detector, 'detect', return_value=Language.JAVASCRIPT):
            result = refactor_service.refactor_file("test.js", RefactorType.GENERAL_CLEANUP)

        assert result.cost_estimate == 0.03
        assert result.tokens_used > 0

    def test_refactor_code_preserves_functionality(self, refactor_service, mock_llm_client):
        """Test that refactoring preserves code functionality."""
        original = "def add(a, b): return a + b"
        refactored = "def add(a: int, b: int) -> int:\n    return a + b"

        mock_llm_client.chat_completion.return_value = {"content": refactored}

        result = refactor_service.refactor_code(original, Language.JAVASCRIPT, RefactorType.GENERAL_CLEANUP)

        # Basic check that core logic is preserved
        assert "def add" in result
        assert "return a + b" in result
