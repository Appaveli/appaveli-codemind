import pytest
from unittest.mock import MagicMock, patch
from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.core.models import RefactorType, Language


@patch("os.path.exists", return_value=True)
@patch("appaveli_codemind.core.agent.FileUtils.read_file", return_value="public class Sample {}")
@patch("appaveli_codemind.core.agent.LanguageDetector.detect", return_value=Language.JAVA)
@patch("appaveli_codemind.core.agent.CodeMindAgent._scan_code_security", return_value=[])
@patch("appaveli_codemind.core.agent.CodeMindAgent._get_code_suggestions", return_value=[])
@patch("appaveli_codemind.core.agent.CodeMindAgent._summarize_code", return_value="Sample summary.")
def test_analyze_file_valid(_, __, ___, ____, _____, ______):
    agent = CodeMindAgent(api_key="test")
    result = agent.analyze_file("Sample.java")

    assert result.language == Language.JAVA
    assert result.summary == "Sample summary."
    assert result.line_count == 1


@patch("appaveli_codemind.core.agent.FileUtils.read_file", return_value="print('Hello')")
@patch("appaveli_codemind.core.agent.LanguageDetector.detect", return_value=Language.JAVASCRIPT)
@patch("appaveli_codemind.core.agent.CodeMindAgent._refactor_code_with_ai", return_value="console.log('Hello');")
def test_refactor_file_valid(_, __, ___):
    agent = CodeMindAgent(api_key="test")
    result = agent.refactor_file("hello.js", RefactorType.GENERAL_CLEANUP)

    assert result.success
    assert "console.log" in result.refactored_code