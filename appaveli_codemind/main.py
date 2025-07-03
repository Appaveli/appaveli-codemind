"""
Appaveli CodeMind - Your Intelligent Code Assistant
Main entry point for the CLI application
"""

import sys
from pathlib import Path

# Add root directory (where bootstrap.py lives) to sys.path
root_path = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_path))

from appaveli_codemind.bootstrap import *

# Add current directory to Python path
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

def main():
    """Main entry point for Appaveli CodeMind"""
    try:
        from appaveli_codemind.cli.commands import cli
        cli()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye from Appaveli CodeMind!")
        sys.exit(0)
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("🔧 Please make sure all dependencies are installed.")
        sys.exit(1)


if __name__ == "__main__":
    main()