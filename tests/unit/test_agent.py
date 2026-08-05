import pytest
from unittest.mock import MagicMock, patch
from datetime import datetime
from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.core.models import AnalysisResult, RefactorResult, RefactorType, Language


def test_analyze_file_valid():
    """Test that analyze_file delegates to AppaveliAnalysisService."""
    agent = CodeMindAgent(api_key="test")

    # Mock the analysis service
    mock_result = AnalysisResult(
        file_path="Sample.java",
        language=Language.JAVA,
        line_count=1,
        security_issues=[],
        code_suggestions=[],
        complexity_score=None,
        maintainability_score=None,
        test_coverage_estimate=None,
        analysis_timestamp=datetime.now(),
        summary="Sample summary."
    )
    agent.analysis_service.analyze_file = MagicMock(return_value=mock_result)

    result = agent.analyze_file("Sample.java")

    assert result.language == Language.JAVA
    assert result.summary == "Sample summary."
    assert result.line_count == 1
    agent.analysis_service.analyze_file.assert_called_once_with("Sample.java")


def test_refactor_file_valid():
    """Test that refactor_file delegates to AppaveliCodeTransform."""
    agent = CodeMindAgent(api_key="test")

    # Mock the code transform service
    mock_result = RefactorResult(
        success=True,
        original_code="print('Hello')",
        refactored_code="console.log('Hello');",
        language=Language.JAVASCRIPT,
        refactor_type=RefactorType.GENERAL_CLEANUP,
        suggestions=[],
        changes_made=["Refactored"],
        tokens_used=10,
        cost_estimate=0.001
    )
    agent.code_transform.refactor_file = MagicMock(return_value=mock_result)

    result = agent.refactor_file("hello.js", RefactorType.GENERAL_CLEANUP)

    assert result.success
    assert "console.log" in result.refactored_code
    agent.code_transform.refactor_file.assert_called_once_with("hello.js", RefactorType.GENERAL_CLEANUP, None)