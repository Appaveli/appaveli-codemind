"""
Validation utilities for Appaveli CodeMind
"""

import os
import re
from pathlib import Path
from typing import Optional


def validate_file_path(file_path: str) -> bool:
    """
    Validate that a file path exists and is accessible
    
    Args:
        file_path: Path to validate
        
    Returns:
        True if file exists and is readable
    """
    try:
        path = Path(file_path)
        return path.exists() and path.is_file() and os.access(file_path, os.R_OK)
    except Exception:
        return False


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate OpenAI API key format, supporting fallback to environment
    """
    key = api_key or os.getenv("OPENAI_API_KEY")
    if not key:
        return False

    return bool(re.match(r'^sk-[a-zA-Z0-9]{48}$', key))


def validate_package_name(package_name: str, language: str) -> bool:
    """
    Validate package name format for different languages
    
    Args:
        package_name: Package name to validate
        language: Programming language
        
    Returns:
        True if package name is valid for the language
    """
    if language.lower() in ['java', 'kotlin']:
        # Java/Kotlin package names: lowercase, dot-separated
        return bool(re.match(r'^[a-z]+(\.[a-z][a-z0-9]*)*$', package_name))
    elif language.lower() == 'swift':
        # Swift module names: PascalCase
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', package_name))
    elif language.lower() in ['javascript', 'typescript']:
        # npm package names: lowercase, hyphens allowed
        return bool(re.match(r'^[a-z][a-z0-9-]*$', package_name))
    
    return True  # Default to valid for other languages


def validate_class_name(class_name: str, language: str) -> bool:
    """
    Validate class name format for different languages
    
    Args:
        class_name: Class name to validate
        language: Programming language
        
    Returns:
        True if class name is valid for the language
    """
    # Most languages use PascalCase for class names
    if language.lower() in ['java', 'kotlin', 'swift', 'cpp', 'dart', 'javascript', 'typescript']:
        return bool(re.match(r'^[A-Z][a-zA-Z0-9]*$', class_name))
    
    return True  # Default to valid
