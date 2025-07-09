# 🧠 Appaveli CodeMind

**Your intelligent code assistant — built for developers who ship in silence.**  
Appaveli CodeMind is an open-source AI-powered CLI tool for rapid, intelligent code analysis, refactoring, security scanning, and test generation across multiple languages.


---

## 🚀 Features

- 🔍 Analyze source code for language, metrics, and issues
- 🔐 Scan projects for security vulnerabilities
- 🧪 Generate unit & integration tests with LLM support
- 🔁 Refactor source files using AI-powered cleanup or style guides
- 🏗️ Boilerplate Generator for data classes, services, and domain models
- 🧠 Supports Java, Kotlin, Swift, C++, Dart, PHP, JavaScript
- 💡 Clean terminal UX with [`rich`](https://github.com/Textualize/rich)

---

## 🛠️ Example Usage

```bash
# Analyze a file with full report
appaveli-codemind analyze -f src/UserController.php

# Just show the summary
appaveli-codemind analyze -f src/UserController.php --summary

# Export pretty HTML or Markdown report
appaveli-codemind analyze -f src/UserController.php --report html
appaveli-codemind analyze -f src/UserController.php --report markdown

# Refactor code using AI
appaveli-codemind refactor -f AuthService.swift -t general_cleanup

# Generate boilerplate (example: Laravel controller)
appaveli-codemind generate -t laravel_controller -n UserController

# Run a full security scan
appaveli-codemind security -p ./myproject
```

---

## 🧩 Architecture

- `main.py` – CLI entry point
- `core/agent.py` – Main orchestration logic
- `core/models.py` – Language + result models
- `core/language_detector.py` – File type classifier
- `ai/llm_client.py` – LLM Client wrapper
- `utils/` – File validation, backup, formatting

---

## ⚙️ Installation

### 🔁 Local (venv)

```bash
python -m venv venv
source venv/bin/activate
pip install -e .
```

### 🌍 Global (with [pipx](https://github.com/pypa/pipx))

```bash
pipx install --editable .
```

---

## 📁 Environment Setup

Create a `.env` file in the project root:

```env
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

---

## 🧪 Example Commands

```bash
# Analyze java file
appaveli-codemind analyze -f Example.java -v

```

---
