# 🧠 Appaveli CodeMind

[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg)](CONTRIBUTING.md)

**AI-powered code intelligence for developers.**

Open-source CLI tool for code analysis, security scanning, intelligent refactoring, and test generation across 8+ programming languages.

---

## ✨ Features

🔍 **AI-Powered Code Analysis**  
Deep analysis of code quality, complexity, and maintainability using GPT-4 and Claude AI.

🔐 **Security Scanning**  
Detect vulnerabilities, security issues, and potential exploits across your codebase.

🧪 **Intelligent Test Generation**  
Automatically generate unit and integration tests with proper assertions and edge cases.

🔁 **AI-Powered Refactoring**  
Improve code quality with context-aware refactoring suggestions and automated cleanup.

🏗️ **Boilerplate Generation**  
Generate production-ready code templates for controllers, models, services, and more.

🌍 **Multi-Language Support**  
Java, Kotlin, Swift, C++, Dart, PHP, JavaScript, TypeScript - with more coming.

💡 **Beautiful Terminal UI**  
Rich, colorful output powered by [`rich`](https://github.com/Textualize/rich) for an excellent developer experience.

📊 **Export Reports**  
Generate professional HTML and Markdown reports for sharing and documentation.

---

## 🚀 Quick Start

### Installation

```bash
# Using pipx (recommended for global install)
pipx install appaveli-codemind

# Or using pip
pip install appaveli-codemind

# Or from source (development)
git clone https://github.com/appaveli/codemind.git
cd codemind
pip install -e .
```

### Basic Usage

```bash
# Analyze a file
appaveli-codemind analyze -f src/UserController.php

# Security scan your project
appaveli-codemind security -p ./backend

# Generate tests
appaveli-codemind test -f src/AuthService.java -o tests/test_auth.java

# Refactor code with AI
appaveli-codemind refactor -f App.swift -t general_cleanup

# Generate boilerplate
appaveli-codemind generate -t spring_controller -n UserController
```

---

## 📖 Examples

### Code Analysis

```bash
# Full analysis with HTML report
appaveli-codemind analyze -f src/UserService.java --report html

# Quick summary
appaveli-codemind analyze -f main.py --summary
```

**Output:**
```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ File Information — main.py      ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Language:       Python          ┃
┃ Lines of code:  156             ┃
┃ Analysis time:  2026-08-03      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

📊 Analysis Results
✅ No security issues found
💡 3 code suggestions
```

### Security Scanning

```bash
# Scan entire project
appaveli-codemind security -p ./backend
```

Detects:
- SQL injection vulnerabilities
- XSS vulnerabilities
- Authentication/authorization issues
- Hardcoded credentials
- Input validation problems

### Test Generation

```bash
# Generate unit tests
appaveli-codemind test -f src/Calculator.java

# Generate integration tests
appaveli-codemind test -f api/users.js -t integration
```

---

## ⚙️ Configuration

### Environment Setup

Create a `.env` file or set environment variables:

```env
# OpenAI Configuration (default)
OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o
OPENAI_MAX_TOKENS=4000

# Or use Anthropic Claude
LLM_PROVIDER=anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929
ANTHROPIC_MAX_TOKENS=4000
```

### LLM Providers

**Supported:**
- **OpenAI** - GPT-4o, GPT-4o-mini (default)
- **Anthropic** - Claude Sonnet 4.5, Claude Opus

Switch providers with `--llm` flag:
```bash
appaveli-codemind analyze -f file.py --llm anthropic
```

---

## 🌍 Supported Languages

| Language       | Analysis | Security | Tests | Refactor | Boilerplate |
|---------------|----------|----------|-------|----------|-------------|
| Java          | ✅       | ✅       | ✅    | ✅       | ✅          |
| Kotlin        | ✅       | ✅       | ✅    | ✅       | ✅          |
| Swift         | ✅       | ✅       | ✅    | ✅       | ✅          |
| C++           | ✅       | ✅       | ✅    | ✅       | ✅          |
| Dart          | ✅       | ✅       | ✅    | ✅       | ✅          |
| PHP           | ✅       | ✅       | ✅    | ✅       | ✅          |
| JavaScript    | ✅       | ✅       | ✅    | ✅       | ✅          |
| TypeScript    | ✅       | ✅       | ✅    | ✅       | ✅          |

**Coming Soon:** Python, Go, Rust, Ruby

Want to add support for another language? See [CONTRIBUTING.md](CONTRIBUTING.md)!

---

## 🏗️ Architecture

```
appaveli_codemind/
├── cli/              # Command-line interface
├── core/             # Core analysis engine
│   ├── agent.py      # Main orchestration
│   ├── models.py     # Data models
│   └── language_detector.py
├── ai/               # LLM integrations
│   ├── openai_client.py
│   └── anthropic_client.py
├── reports/          # Report generators
├── utils/            # Utilities
└── web_api/          # Web API
```

---

## 🤝 Contributing

We love contributions! Whether it's:

- 🐛 Bug reports
- 💡 Feature requests
- 📝 Documentation improvements
- 🔧 Code contributions
- 🌍 Adding language support

Please read our [Contributing Guidelines](CONTRIBUTING.md) to get started.

### Quick Contribution Setup

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/codemind.git
cd codemind

# Set up development environment
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest tests/ -v

# Format code
black appaveli_codemind/
isort appaveli_codemind/
```

### High-Impact Areas

Want to make a big contribution? These areas need help:

**Core Engine:**
- [ ] Add support for more languages (Python, Go, Rust, Ruby)
- [ ] Improve security rule detection
- [ ] Better test generation logic
- [ ] Refactoring pattern improvements

**CLI Experience:**
- [ ] Interactive mode
- [ ] Configuration file support
- [ ] Better error messages
- [ ] Progress indicators for large projects

**Integrations:**
- [ ] VS Code extension
- [ ] GitHub Action
- [ ] Pre-commit hook
- [ ] Docker image

See our [Issues](https://github.com/appaveli/codemind/issues) for specific tasks.

---

## 🗺️ Roadmap

### Current Version: 1.3.0

### Upcoming Features

**v1.4 - CLI Improvements**
- [ ] Interactive mode
- [ ] Configuration file support (.codemind.yaml)
- [ ] Watch mode for continuous analysis
- [ ] Better caching for faster re-analysis

**v1.4 - Language Expansion**
- [ ] Python support
- [ ] Go support
- [ ] Rust support
- [ ] Ruby support

**v1.5 - Advanced Features**
- [ ] Custom security rules
- [ ] Plugin system
- [ ] Multi-file refactoring
- [ ] Dependency analysis

**v2.0 - Major Release**
- [ ] Repository-level analysis
- [ ] Architecture visualization
- [ ] Improved performance
- [ ] Enhanced reporting

---

## 💬 Community

- **GitHub Discussions** - [Ask questions, share ideas](https://github.com/appaveli/codemind/discussions)
- **Issues** - [Report bugs, request features](https://github.com/appaveli/codemind/issues)
- **Twitter** - [@AppaveliTech](https://twitter.com/AppaveliTech)
- **Email** - support@appaveli.com

---

## 🐛 Report Issues

Found a bug or have a suggestion?

- **Bug Report** - [Create an issue](https://github.com/appaveli/codemind/issues/new)
- **Feature Request** - [Suggest a feature](https://github.com/appaveli/codemind/issues/new)
- **Security Issue** - Email security@appaveli.com (do not create public issues)

---

## 📜 License

CodeMind is open source and licensed under the [MIT License](LICENSE).

```
Copyright (c) 2026 Dominque Terry / Appaveli Tech Solutions, LLC

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software...
```

---

## 🙏 Acknowledgments

Built with:
- [OpenAI](https://openai.com) - GPT-4 models for code intelligence
- [Anthropic](https://anthropic.com) - Claude AI for advanced analysis
- [Rich](https://github.com/Textualize/rich) - Beautiful terminal UI
- [Click](https://click.palletsprojects.com/) - CLI framework
- [FastAPI](https://fastapi.tiangolo.com/) - Web API framework

Special thanks to all our [contributors](https://github.com/appaveli/codemind/graphs/contributors)!

---

## ⭐ Star History

If you find CodeMind useful, please give us a star! It helps others discover the project.

[![Star History Chart](https://api.star-history.com/svg?repos=appaveli/codemind&type=Date)](https://star-history.com/#appaveli/codemind&Date)

---

## 🚀 Get Started

```bash
# Install CodeMind
pipx install appaveli-codemind

# Analyze your code
appaveli-codemind analyze -f your-code.java

# Join the community
# ⭐ Star the repo
# 💬 Join discussions
# 🔧 Contribute code
# 📣 Spread the word
```

---

**Made with ❤️ by developers, for developers.**
