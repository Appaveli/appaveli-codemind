"""
Appaveli CodeMind - Your Intelligent Code Assistant

A powerful multi-language AI code agent for refactoring, security scanning,
boilerplate generation, and test creation.
"""

__version__ = "0.1.0"
__author__ = "AppaveliTech Solutions"
__email__ = "support@appaveli.com"
__description__ = "AI-powered code refactoring, security scanning, and generation"

from appaveli_codemind.core.agent import CodeMindAgent
from appaveli_codemind.core.models import Language, BoilerplateType, SecurityIssue

__all__ = [
    "CodeMindAgent",
    "Language", 
    "BoilerplateType",
    "SecurityIssue",
    "__version__",
]