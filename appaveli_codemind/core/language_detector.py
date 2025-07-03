"""
Language detection utilities for Appaveli CodeMind
"""

import os
import re
from pathlib import Path
from typing import Optional, Dict, List
from core.models import Language


class LanguageDetector:
    """Detect programming language from file extension and content"""
    
    # File extension to language mapping
    EXTENSIONS = {
        '.java': Language.JAVA,
        '.kt': Language.KOTLIN,
        '.kts': Language.KOTLIN,
        '.swift': Language.SWIFT,
        '.cpp': Language.CPP,
        '.cc': Language.CPP,
        '.cxx': Language.CPP,
        '.c++': Language.CPP,
        '.hpp': Language.CPP,
        '.h': Language.CPP,
        '.dart': Language.DART,
        '.js': Language.JAVASCRIPT,
        '.jsx': Language.JAVASCRIPT,
        '.ts': Language.TYPESCRIPT,
        '.tsx': Language.TYPESCRIPT,
        '.mjs': Language.JAVASCRIPT,
    }
    
    # Content-based detection patterns
    CONTENT_PATTERNS = {
        Language.JAVA: [
            r'package\s+[\w.]+;',
            r'import\s+[\w.]+;',
            r'public\s+class\s+\w+',
            r'@Override',
        ],
        Language.KOTLIN: [
            r'package\s+[\w.]+',
            r'import\s+[\w.]+',
            r'class\s+\w+',
            r'fun\s+\w+',
            r'val\s+\w+',
            r'var\s+\w+',
        ],
        Language.SWIFT: [
            r'import\s+\w+',
            r'class\s+\w+',
            r'struct\s+\w+',
            r'func\s+\w+',
            r'var\s+\w+',
            r'let\s+\w+',
        ],
        Language.CPP: [
            r'#include\s*<[\w./]+>',
            r'#include\s*"[\w./]+"',
            r'namespace\s+\w+',
            r'class\s+\w+',
            r'std::',
        ],
        Language.DART: [
            r'import\s+[\'"][\w./]+[\'"];',
            r'class\s+\w+',
            r'void\s+main\(',
            r'Widget\s+build\(',
            r'@override',
        ],
        Language.JAVASCRIPT: [
            r'function\s+\w+',
            r'const\s+\w+',
            r'let\s+\w+',
            r'var\s+\w+',
            r'require\([\'"][\w./]+[\'"]\)',
            r'import\s+.*from\s+[\'"][\w./]+[\'"]',
        ],
        Language.TYPESCRIPT: [
            r'interface\s+\w+',
            r'type\s+\w+',
            r'export\s+interface',
            r'export\s+type',
            r':\s*\w+(\[\])?(\s*\|\s*\w+)*',  # Type annotations
        ],
    }
    
    @classmethod
    def detect(cls, file_path: str) -> Optional[Language]:
        """
        Detect programming language from file path and content
        
        Args:
            file_path: Path to the file to analyze
            
        Returns:
            Detected Language enum or None if not supported
        """
        if not os.path.exists(file_path):
            return None
            
        # First try extension-based detection
        path = Path(file_path)
        extension_lang = cls.EXTENSIONS.get(path.suffix.lower())
        
        # If we have a definitive match from extension, use it
        if extension_lang and extension_lang != Language.JAVASCRIPT:
            return extension_lang
            
        # For ambiguous cases (like .js vs .ts) or unknown extensions,
        # use content-based detection
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read(8192)  # Read first 8KB for performance
                
            content_lang = cls._detect_from_content(content)
            
            # Prefer content detection for JS/TS disambiguation
            if content_lang:
                return content_lang
                
            # Fall back to extension detection
            return extension_lang
            
        except Exception:
            # If we can't read the file, fall back to extension
            return extension_lang
    
    @classmethod
    def _detect_from_content(cls, content: str) -> Optional[Language]:
        """
        Detect language from file content using pattern matching
        
        Args:
            content: File content to analyze
            
        Returns:
            Detected Language enum or None
        """
        scores = {}
        
        # Score each language based on pattern matches
        for language, patterns in cls.CONTENT_PATTERNS.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, content, re.MULTILINE | re.IGNORECASE))
                score += matches
            
            if score > 0:
                scores[language] = score
        
        # Return language with highest score
        if scores:
            return max(scores, key=scores.get)
        
        return None
    
    @classmethod
    def get_supported_extensions(cls) -> List[str]:
        """Get list of all supported file extensions"""
        return list(cls.EXTENSIONS.keys())
    
    @classmethod
    def get_supported_languages(cls) -> List[Language]:
        """Get list of all supported languages"""
        return list(set(cls.EXTENSIONS.values()))
    
    @classmethod
    def is_supported_file(cls, file_path: str) -> bool:
        """Check if a file is supported by CodeMind"""
        return cls.detect(file_path) is not None