# Contributing to CodeMind

First off, thank you for considering contributing to CodeMind! 🎉

CodeMind is an open-source AI-powered code analysis tool, and we welcome contributions from developers of all skill levels.

## 🌟 Ways to Contribute

- 🐛 **Report bugs** - Help us identify and fix issues
- 💡 **Suggest features** - Share ideas for new functionality
- 📝 **Improve documentation** - Make it easier for others to use CodeMind
- 🔧 **Submit code** - Fix bugs or implement new features
- ✅ **Write tests** - Help us maintain code quality
- 🌍 **Add language support** - Extend CodeMind to new programming languages

## 🚀 Quick Start

### 1. Fork & Clone

```bash
# Fork the repo on GitHub, then:
git clone https://github.com/YOUR_USERNAME/codemind.git
cd codemind
```

### 2. Set Up Development Environment

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Create a Branch

```bash
git checkout -b feature/your-feature-name
# or
git checkout -b fix/bug-description
```

### 4. Make Changes

- Write your code
- Add tests for new functionality
- Update documentation if needed
- Ensure all tests pass

### 5. Run Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=appaveli_codemind --cov-report=html

# Open coverage report
open htmlcov/index.html
```

### 6. Code Quality Checks

```bash
# Format code
black appaveli_codemind/ tests/
isort appaveli_codemind/ tests/

# Lint
flake8 appaveli_codemind/

# Type check (optional but recommended)
mypy appaveli_codemind/
```

Pre-commit hooks will run these automatically when you commit.

### 7. Commit Your Changes

```bash
# Stage changes
git add .

# Commit with descriptive message
git commit -m "feat: add support for Go language analysis"

# Or for bug fixes:
git commit -m "fix: resolve issue with PHP file detection"
```

**Commit Message Format:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation changes
- `test:` - Adding tests
- `refactor:` - Code refactoring
- `chore:` - Maintenance tasks

### 8. Push & Create Pull Request

```bash
# Push to your fork
git push origin feature/your-feature-name

# Go to GitHub and create a Pull Request
```

## 📋 Pull Request Guidelines

### Before Submitting

- [ ] All tests pass locally
- [ ] Code is formatted with `black` and `isort`
- [ ] New features have tests
- [ ] Documentation is updated
- [ ] Commit messages are clear and descriptive

### PR Description Should Include

1. **What** - What does this PR do?
2. **Why** - Why is this change needed?
3. **How** - How does it work?
4. **Testing** - How did you test it?

**Example:**
```markdown
## What
Adds support for analyzing Rust (.rs) files

## Why
Many users requested Rust support (#123)

## How
- Added Rust language enum
- Implemented Rust-specific patterns in language detector
- Added Rust security rules

## Testing
- Added 15 unit tests for Rust detection
- Tested with sample Rust projects
- All existing tests still pass
```

### Review Process

1. Maintainer will review within 48 hours
2. Address any feedback
3. Once approved, we'll merge!

## 🧪 Writing Tests

We aim for **70%+ test coverage**. Every new feature should have tests.

### Test Structure

```
tests/
├── unit/              # Fast, isolated tests
│   ├── core/
│   ├── ai/
│   └── utils/
├── integration/       # Tests with real file I/O
└── fixtures/          # Sample code files
```

### Example Test

```python
# tests/unit/core/test_language_detector.py
import pytest
from appaveli_codemind.core.language_detector import LanguageDetector
from appaveli_codemind.core.models import Language

def test_detect_python_file():
    detector = LanguageDetector()
    language = detector.detect("example.py")
    assert language == Language.PYTHON

def test_detect_java_file_by_content():
    detector = LanguageDetector()
    # Test content-based detection
    content = "public class Example { }"
    language = detector._detect_from_content(content)
    assert language == Language.JAVA
```

## 📝 Code Style

We use:
- **Black** for formatting (line length: 100)
- **isort** for import sorting
- **flake8** for linting
- **Type hints** for public APIs

### Example

```python
from typing import List, Optional
from appaveli_codemind.core.models import Language, AnalysisResult

def analyze_file(
    file_path: str,
    language: Optional[Language] = None,
    options: Optional[dict] = None
) -> AnalysisResult:
    """
    Analyze a code file for issues and metrics.
    
    Args:
        file_path: Path to the file to analyze
        language: Optional language override
        options: Optional analysis configuration
        
    Returns:
        AnalysisResult with findings and metrics
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file type is not supported
    """
    # Implementation here
    pass
```

## 🐛 Reporting Bugs

Found a bug? Please create an issue with:

1. **Description** - What happened?
2. **Expected behavior** - What should happen?
3. **Steps to reproduce**
   ```
   1. Run `appaveli-codemind analyze -f test.py`
   2. See error
   ```
4. **Environment**
   - OS: macOS 14.0
   - Python: 3.11.5
   - CodeMind version: 1.1.0
5. **Logs/Screenshots** - If applicable

## 💡 Suggesting Features

We love new ideas! Create an issue with:

1. **Problem** - What problem does this solve?
2. **Proposed solution** - How would it work?
3. **Alternatives** - Other approaches considered?
4. **Additional context** - Examples, mockups, etc.

## 🏗️ Adding Language Support

Want to add support for a new programming language?

### Steps:

1. Add language to `Language` enum in `core/models.py`
2. Add file extensions to `LanguageDetector.EXTENSIONS`
3. Add content patterns to `LanguageDetector.CONTENT_PATTERNS`
4. Add test framework mapping (if supporting test generation)
5. Write tests with sample files
6. Update documentation

**Example PR:** See #42 (hypothetical - added Go support)

## 🔒 Security Issues

**Do NOT** create public issues for security vulnerabilities.

Instead, email: **support@appaveli.tech**

We'll respond within 48 hours and work with you on a fix.

## 📜 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

All contributors will be:
- Listed in our README
- Mentioned in release notes
- Invited to our Discord community

## 💬 Questions?

- **GitHub Discussions** - Ask questions, share ideas
- **Discord** - Join our community (link in README)
- **Email** - contact@appaveli.tech

## 🎯 Good First Issues

New to open source? Look for issues labeled `good first issue`:

https://github.com/Appaveli/appaveli-codemind/labels/good%20first%20issue

These are specifically chosen to be beginner-friendly!

---

**Thank you for contributing to CodeMind!** 🚀

Every contribution, no matter how small, makes a difference.
