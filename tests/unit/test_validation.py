import os
from unittest.mock import patch
import pytest
from appaveli_codemind.utils.validation import (
    validate_file_path,
    validate_api_key,
    validate_package_name,
    validate_class_name,
)


@patch("appaveli_codemind.utils.validation.Path.exists", return_value=True)
@patch("appaveli_codemind.utils.validation.Path.is_file", return_value=True)
@patch("appaveli_codemind.utils.validation.os.access", return_value=True)
def test_validate_file_path_valid(mock_access, mock_is_file, mock_exists):
    assert validate_file_path("some/file/path.java") is True


@patch("appaveli_codemind.utils.validation.Path.exists", return_value=False)
def test_validate_file_path_invalid(mock_exists):
    assert validate_file_path("invalid/file.java") is False




def test_validate_package_name_java_valid():
    assert validate_package_name("com.appaveli.utils", "java") is True


def test_validate_package_name_java_invalid():
    assert not validate_package_name("com.Appaveli.Utils", "java")


def test_validate_package_name_swift_valid():
    assert validate_package_name("AppaveliKit", "swift") is True


def test_validate_package_name_swift_invalid():
    assert not validate_package_name("appaveli_kit", "swift")


def test_validate_package_name_js_valid():
    assert validate_package_name("appaveli-cli", "javascript") is True


def test_validate_package_name_js_invalid():
    assert not validate_package_name("Appaveli-CLI", "typescript")


def test_validate_class_name_valid():
    assert validate_class_name("MyService", "java") is True


def test_validate_class_name_invalid():
    assert not validate_class_name("myService", "kotlin")


def test_validate_class_name_other_langs():
    assert validate_class_name("WhateverName", "ruby") is True