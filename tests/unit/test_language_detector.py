import pytest
from unittest.mock import patch, mock_open
from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language


@pytest.mark.parametrize("file_path, extension, expected", [
    ("MyClass.java", ".java", Language.JAVA),
    ("main.kt", ".kt", Language.KOTLIN),
    ("script.dart", ".dart", Language.DART),
    ("index.ts", ".ts", Language.TYPESCRIPT),
    ("controller.php", ".php", Language.PHP),
])
@patch("os.path.exists", return_value=True)
def test_detect_by_extension(mock_exists, file_path, extension, expected):
    result = LanguageDetector.detect(file_path)
    assert result == expected


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="<?php echo 'Hello'; class Test {} function doSomething() {} ?>")
def test_detect_by_content_php(mock_file, mock_exists):
    result = LanguageDetector.detect("somefile.unknown")
    assert result == Language.PHP


@patch("os.path.exists", return_value=True)
@patch("builtins.open", new_callable=mock_open, read_data="fun main() { val name = \"Kotlin\" }")
def test_detect_by_content_kotlin(mock_file, mock_exists):
    result = LanguageDetector.detect("unknown.xyz")
    assert result == Language.KOTLIN


@patch("os.path.exists", return_value=False)
def test_detect_returns_none_for_missing_file(mock_exists):
    result = LanguageDetector.detect("nonexistent.file")
    assert result is None


def test_get_supported_extensions():
    exts = LanguageDetector.get_supported_extensions()
    assert ".java" in exts
    assert ".php" in exts


def test_get_supported_languages():
    langs = LanguageDetector.get_supported_languages()
    assert Language.JAVA in langs
    assert Language.PHP in langs


@patch.object(LanguageDetector, "detect", return_value=Language.SWIFT)
def test_is_supported_file_true(mock_detect):
    assert LanguageDetector.is_supported_file("dummy.swift")


@patch.object(LanguageDetector, "detect", return_value=None)
def test_is_supported_file_false(mock_detect):
    assert not LanguageDetector.is_supported_file("file.unknown")